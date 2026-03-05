#!/usr/bin/env python3
"""
Eidolon Search HTTP API Server

AIRI 등 외부 시스템에서 Eidolon 메모리를 사용할 수 있게 하는 REST API.
논문의 "무의식 레이어"를 HTTP 서비스로 노출.

Endpoints:
  POST /search           - 인간형 기억 검색 (FTS5 + 메타데이터)
  POST /remember         - 새 기억 저장
  POST /consolidate      - 기억 공고화 (수동 트리거)
  GET  /memory/:path     - 특정 기억 조회
  GET  /stats            - 메모리 시스템 통계

Usage:
  python scripts/api-server.py [--port 8384] [--db ./memory.db]

AIRI 연동:
  이 서버를 띄우면 AIRI의 메모리 모듈에서 HTTP로 호출 가능.
  "정체성은 중앙에, I/O는 분산으로" 원칙.
"""

import os
import sys
import json
import time
import sqlite3
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import search/consolidation from sibling scripts
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

DB_PATH = os.environ.get('DB_PATH', './memory.db')


def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


class EidolonHandler(BaseHTTPRequestHandler):
    db_path = DB_PATH
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))
    
    def do_OPTIONS(self):
        self._send_json({})
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/stats':
            self._handle_stats()
        elif path.startswith('/memory/'):
            mem_path = path[8:]  # strip /memory/
            self._handle_get_memory(mem_path)
        elif path == '/health':
            self._send_json({'status': 'ok', 'version': '0.1.0'})
        else:
            self._send_json({'error': 'not found'}, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/search':
            self._handle_search()
        elif path == '/remember':
            self._handle_remember()
        elif path == '/consolidate':
            self._handle_consolidate()
        else:
            self._send_json({'error': 'not found'}, 404)
    
    def _handle_search(self):
        """인간형 기억 검색"""
        body = self._read_body()
        query = body.get('query', '')
        limit = body.get('limit', 10)
        valence = body.get('valence', 0.0)
        
        if not query:
            self._send_json({'error': 'query required'}, 400)
            return
        
        # search-v2 import
        try:
            search_mod = import_module('search-v2')
            results = search_mod.hybrid_search(query, limit, valence, self.db_path)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
            return
        
        self._send_json({
            'query': query,
            'valence': valence,
            'results': results,
            'count': len(results),
        })
    
    def _handle_remember(self):
        """새 기억 저장"""
        body = self._read_body()
        path = body.get('path', '')
        content = body.get('content', '')
        valence = body.get('valence', 0.0)
        arousal = body.get('arousal', 0.5)
        source = body.get('source', 'text')
        tags = body.get('tags', [])
        social = body.get('social', [])
        
        if not path or not content:
            self._send_json({'error': 'path and content required'}, 400)
            return
        
        try:
            conn = get_db(self.db_path)
            c = conn.cursor()
            now = time.time()
            
            # FTS5에 저장
            c.execute("""
            INSERT OR REPLACE INTO memory_fts (path, content)
            VALUES (?, ?)
            """, (path, content))
            
            # 메타데이터 저장
            c.execute("""
            INSERT OR REPLACE INTO memory_meta 
            (path, created_at, valence, arousal, source, tags, social, strength)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1.0)
            """, (path, now, valence, arousal, source,
                  json.dumps(tags, ensure_ascii=False),
                  json.dumps(social, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
            
            self._send_json({
                'stored': True,
                'path': path,
                'timestamp': now,
            })
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_consolidate(self):
        """기억 공고화 (수동 트리거)"""
        try:
            consolidation_mod = import_module('consolidation')
            stats = consolidation_mod.consolidate(self.db_path, verbose=False)
            self._send_json({
                'consolidated': True,
                'stats': stats,
            })
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_get_memory(self, mem_path):
        """특정 기억 조회"""
        try:
            conn = get_db(self.db_path)
            
            # FTS5에서 content
            row = conn.execute("""
            SELECT content FROM memory_fts WHERE path = ?
            """, (mem_path,)).fetchone()
            
            if not row:
                conn.close()
                self._send_json({'error': 'memory not found'}, 404)
                return
            
            # 메타데이터
            meta = conn.execute("""
            SELECT * FROM memory_meta WHERE path = ?
            """, (mem_path,)).fetchone()
            
            # 연결된 기억
            links = conn.execute("""
            SELECT target_path, link_type, strength 
            FROM memory_links WHERE source_path = ?
            UNION
            SELECT source_path, link_type, strength
            FROM memory_links WHERE target_path = ?
            """, (mem_path, mem_path)).fetchall()
            
            conn.close()
            
            result = {
                'path': mem_path,
                'content': row['content'],
                'meta': dict(meta) if meta else None,
                'links': [dict(l) for l in links],
            }
            
            self._send_json(result)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_stats(self):
        """메모리 시스템 통계"""
        try:
            conn = get_db(self.db_path)
            
            total = conn.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0]
            with_meta = conn.execute("SELECT COUNT(*) FROM memory_meta").fetchone()[0]
            links = conn.execute("SELECT COUNT(*) FROM memory_links").fetchone()[0]
            recalls = conn.execute("SELECT COUNT(*) FROM recall_log").fetchone()[0]
            
            avg_strength = conn.execute(
                "SELECT AVG(strength) FROM memory_meta"
            ).fetchone()[0]
            
            avg_valence = conn.execute(
                "SELECT AVG(valence) FROM memory_meta"
            ).fetchone()[0]
            
            conn.close()
            
            self._send_json({
                'total_memories': total,
                'with_metadata': with_meta,
                'links': links,
                'total_recalls': recalls,
                'avg_strength': round(avg_strength or 0, 3),
                'avg_valence': round(avg_valence or 0, 3),
                'version': '0.1.0',
            })
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def log_message(self, format, *args):
        """Suppress default logging, use custom"""
        pass


def main():
    parser = argparse.ArgumentParser(description='Eidolon Search API Server')
    parser.add_argument('--port', type=int, default=8384, help='Port (default: 8384)')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--host', default='0.0.0.0', help='Bind host')
    args = parser.parse_args()
    
    EidolonHandler.db_path = args.db
    
    server = HTTPServer((args.host, args.port), EidolonHandler)
    print(f"🧠 Eidolon Search API Server v0.1.0")
    print(f"   DB: {args.db}")
    print(f"   Listening on {args.host}:{args.port}")
    print(f"   Endpoints:")
    print(f"     POST /search         - Human-like memory search")
    print(f"     POST /remember       - Store new memory")
    print(f"     POST /consolidate    - Trigger consolidation")
    print(f"     GET  /memory/:path   - Get specific memory")
    print(f"     GET  /stats          - Memory system stats")
    print(f"     GET  /health         - Health check")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
