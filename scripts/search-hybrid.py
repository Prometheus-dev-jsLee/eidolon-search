#!/usr/bin/env python3
"""
Eidolon Search v0.2.0 - Hybrid Memory Search

Dual-pathway search: FTS5 keyword (precise) + Qdrant vector (semantic)
Based on the memory-vector paper: "벡터는 기억 자체가 아니라 열쇠(key)다"

The paper's insight: 384 dimensions match human long-term memory compression.
FTS5 = conscious keyword recall. Qdrant = unconscious semantic similarity.

Usage:
  python scripts/search-hybrid.py "query" [--limit 10] [--valence 0.5]
  python scripts/search-hybrid.py "Physical AI roadmap" --mode hybrid
  python scripts/search-hybrid.py "그때 행복했던 기억" --mode vector --valence 0.8
"""

import sys
import os
import json
import math
import sqlite3
import time
import argparse
from pathlib import Path

# Load .env.qdrant
WORKSPACE = Path(__file__).parent.parent
env_path = WORKSPACE.parent / ".env.qdrant"
if not env_path.exists():
    env_path = WORKSPACE / ".env.qdrant"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DB_PATH = os.environ.get('DB_PATH', str(WORKSPACE / 'memory.db'))
QDRANT_URL = os.environ.get('QDRANT_URL', '')
QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY', '')
QDRANT_COLLECTION = os.environ.get('QDRANT_COLLECTION', 'long_term_memory')

# Embedding model
EMBED_MODEL = "all-MiniLM-L6-v2"


def get_qdrant_client():
    """Lazy init Qdrant client"""
    if not QDRANT_URL:
        return None
    try:
        from qdrant_client import QdrantClient
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=15)
    except Exception as e:
        print(f"⚠️ Qdrant unavailable: {e}")
        return None


def get_embedding(text):
    """Generate 384-dim embedding using sentence-transformers"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBED_MODEL)
        return model.encode(text).tolist()
    except ImportError:
        print("⚠️ sentence-transformers not installed. pip install sentence-transformers")
        return None


def compute_decay(decay_rate, days_elapsed):
    """Ebbinghaus forgetting curve approximation"""
    if days_elapsed <= 0:
        return 1.0
    return max(0.01, (decay_rate or 0.95) ** (days_elapsed / 7.0))


def fts_search(query, limit=30, db_path=DB_PATH):
    """FTS5 keyword search — conscious recall pathway"""
    if not Path(db_path).exists():
        return []
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    results = c.execute("""
    SELECT 
        path,
        snippet(memory_fts, 1, '[', ']', '...', 30) as snippet,
        rank
    FROM memory_fts
    WHERE memory_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """, (query, limit)).fetchall()
    
    conn.close()
    return [{'path': r[0], 'snippet': r[1], 'fts_rank': r[2], 'source': 'fts5'} for r in results]


def vector_search(query, limit=30, collections=None):
    """Qdrant vector search — unconscious semantic pathway"""
    client = get_qdrant_client()
    if not client:
        return []
    
    embedding = get_embedding(query)
    if not embedding:
        return []
    
    if collections is None:
        collections = [QDRANT_COLLECTION]
    
    results = []
    for coll_name in collections:
        try:
            response = client.query_points(
                collection_name=coll_name,
                query=embedding,
                limit=limit,
                with_payload=True,
            )
            hits = response.points if hasattr(response, 'points') else response
            for hit in hits:
                payload = hit.payload or {}
                results.append({
                    'path': payload.get('path', payload.get('source', f'qdrant:{coll_name}')),
                    'snippet': payload.get('content', payload.get('text', ''))[:200],
                    'vector_score': hit.score,
                    'collection': coll_name,
                    'source': 'qdrant',
                    'payload': payload,
                })
        except Exception as e:
            print(f"⚠️ Qdrant search error ({coll_name}): {e}")
    
    return results


def get_metadata(path, db_path=DB_PATH):
    """Get memory metadata from SQLite (if exists)"""
    if not Path(db_path).exists():
        return None
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        meta = c.execute("""
        SELECT valence, arousal, decay_rate, consolidation, 
               strength, created_at, last_recalled
        FROM memory_meta WHERE path = ?
        """, (path,)).fetchone()
        conn.close()
        if meta:
            return {
                'valence': meta[0], 'arousal': meta[1], 'decay_rate': meta[2],
                'consolidation': meta[3], 'strength': meta[4],
                'created_at': meta[5], 'last_recalled': meta[6],
            }
    except sqlite3.OperationalError:
        pass
    return None


def hybrid_search(query, limit=10, current_valence=0.0, mode='hybrid',
                  db_path=DB_PATH, collections=None):
    """
    Dual-pathway hybrid search:
    
    Paper insight: "벡터는 기억 자체가 아니라 기억을 찾아가는 열쇠"
    - FTS5 = precise keyword recall (의식적 검색)
    - Qdrant = semantic similarity (무의식적 연상)
    - Metadata = emotional/temporal weighting (인간적 편향)
    
    Scoring formula from the paper:
      score = semantic × 0.30 + keyword × 0.25 + emotion × 0.15 
            + recency × 0.10 + reinforcement × 0.10 + decay × 0.10
    """
    now = time.time()
    
    # Gather candidates from both pathways
    fts_results = []
    vec_results = []
    
    if mode in ('hybrid', 'fts', 'keyword'):
        fts_results = fts_search(query, limit=limit * 3, db_path=db_path)
    
    if mode in ('hybrid', 'vector', 'semantic'):
        vec_results = vector_search(query, limit=limit * 3, collections=collections)
    
    # Merge by path (deduplicate)
    candidates = {}
    
    for r in fts_results:
        path = r['path']
        if path not in candidates:
            candidates[path] = {'path': path, 'snippet': r['snippet'], 'sources': []}
        candidates[path]['fts_rank'] = r['fts_rank']
        candidates[path]['sources'].append('fts5')
    
    for r in vec_results:
        path = r['path']
        if path not in candidates:
            candidates[path] = {'path': path, 'snippet': r['snippet'], 'sources': []}
        candidates[path]['vector_score'] = r.get('vector_score', 0)
        candidates[path]['collection'] = r.get('collection', '')
        if 'qdrant' not in candidates[path]['sources']:
            candidates[path]['sources'].append('qdrant')
    
    # Score each candidate
    scored = []
    for path, cand in candidates.items():
        meta = get_metadata(path, db_path) or {}
        
        # Component scores
        
        # 1. Keyword precision (FTS5)
        fts_rank = cand.get('fts_rank', -999)
        keyword_score = 1.0 / (1.0 + abs(fts_rank)) if fts_rank != -999 else 0.0
        
        # 2. Semantic similarity (Qdrant cosine)
        semantic_score = cand.get('vector_score', 0.0)
        
        # 3. Emotional affinity
        valence = meta.get('valence', 0.0) or 0.0
        emotion_score = 1.0 - abs(current_valence - valence)
        
        # 4. Recency
        created_at = meta.get('created_at', now) or now
        days_ago = (now - created_at) / 86400
        recency_score = 1.0 / (1.0 + days_ago * 0.1)
        
        # 5. Reinforcement (consolidation count)
        consolidation = meta.get('consolidation', 0) or 0
        reinforcement = math.log(1 + consolidation) * 0.1
        
        # 6. Decay (forgetting curve)
        decay_rate = meta.get('decay_rate', 0.95) or 0.95
        last_recalled = meta.get('last_recalled', created_at) or created_at
        days_since_recall = (now - last_recalled) / 86400
        decay = compute_decay(decay_rate, days_since_recall)
        
        # Dual-source bonus: found by BOTH pathways = stronger memory
        dual_bonus = 0.15 if len(cand['sources']) > 1 else 0.0
        
        # Composite score (paper formula + dual bonus)
        final_score = (
            semantic_score   * 0.30
            + keyword_score  * 0.25
            + emotion_score  * 0.15
            + recency_score  * 0.10
            + reinforcement  * 0.10
            + decay          * 0.10
            + dual_bonus
        )
        
        scored.append({
            'path': path,
            'snippet': cand['snippet'],
            'score': round(final_score, 4),
            'sources': cand['sources'],
            'components': {
                'semantic': round(semantic_score, 3),
                'keyword': round(keyword_score, 3),
                'emotion': round(emotion_score, 3),
                'recency': round(recency_score, 3),
                'reinforcement': round(reinforcement, 3),
                'decay': round(decay, 3),
                'dual_bonus': round(dual_bonus, 3),
            },
            'meta': {
                'valence': valence,
                'consolidation': consolidation,
                'days_ago': round(days_ago, 1),
            }
        })
    
    # Sort by composite score
    scored.sort(key=lambda x: x['score'], reverse=True)
    
    # Log recalls
    if Path(db_path).exists():
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            for result in scored[:limit]:
                try:
                    c.execute("""
                    INSERT INTO recall_log (path, query, score, recalled_at)
                    VALUES (?, ?, ?, ?)
                    """, (result['path'], query, result['score'], now))
                    c.execute("""
                    UPDATE memory_meta 
                    SET consolidation = consolidation + 1, last_recalled = ?
                    WHERE path = ?
                    """, (now, result['path']))
                except sqlite3.OperationalError:
                    pass
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    return scored[:limit]


def main():
    parser = argparse.ArgumentParser(description='Eidolon Hybrid Memory Search')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--valence', type=float, default=0.0, help='Current emotional state (-1 to 1)')
    parser.add_argument('--mode', choices=['hybrid', 'fts', 'vector'], default='hybrid')
    parser.add_argument('--db', default=DB_PATH)
    parser.add_argument('--collections', nargs='+', default=None,
                        help='Qdrant collections to search')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    start = time.time()
    results = hybrid_search(
        args.query, limit=args.limit, current_valence=args.valence,
        mode=args.mode, db_path=args.db, collections=args.collections
    )
    elapsed = time.time() - start
    
    if args.json:
        print(json.dumps({'results': results, 'elapsed_ms': round(elapsed * 1000, 1)}, 
                         ensure_ascii=False, indent=2))
        return
    
    print(f"\n🔍 Hybrid search: \"{args.query}\" (mode={args.mode}, {elapsed*1000:.0f}ms)")
    print(f"   Found {len(results)} results\n")
    
    for i, r in enumerate(results):
        sources = '+'.join(r['sources'])
        comp = r['components']
        print(f"  [{i+1}] {r['path']}")
        print(f"      Score: {r['score']} ({sources})")
        print(f"      S:{comp['semantic']} K:{comp['keyword']} E:{comp['emotion']} "
              f"R:{comp['recency']} +:{comp['reinforcement']} D:{comp['decay']}")
        if comp['dual_bonus'] > 0:
            print(f"      ★ Dual-source bonus: +{comp['dual_bonus']}")
        print(f"      {r['snippet'][:120]}...")
        print()


if __name__ == '__main__':
    main()
