#!/usr/bin/env python3
"""
검색 성능 비교 스크립트

기존 방식 vs 새 방식 비교:
- 시간 측정
- 토큰 추정
- 결과 개수
- DB 기록

사용법:
  python3 compare-search.py "검색어"
  python3 compare-search.py "검색어" --session-tokens 50000
"""

import time
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
DB_PATH = WORKSPACE / "documents.db"

def estimate_tokens(text):
    """토큰 수 추정 (간단: 단어 * 1.3)"""
    return int(len(text.split()) * 1.3)

def search_old_way(query):
    """기존 방식 시뮬레이션 (memory_search)"""
    start = time.time()
    
    # memory_search 시뮬레이션
    # 실제로는 memory_search tool 사용하지만,
    # 여기서는 유사한 동작 시뮬레이션
    
    # 1. 전체 daily notes 검색 (가정: 평균 50개 파일)
    files_read = 0
    total_tokens = 0
    found = 0
    
    # 간단히: documents.db에서 Daily/* 파일들 검색
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    results = c.execute("""
    SELECT path, content
    FROM documents
    WHERE path LIKE '%Daily/%'
      AND lower(content) LIKE lower(?)
    LIMIT 10
    """, (f"%{query}%",)).fetchall()
    
    for path, content in results:
        files_read += 1
        # 전체 파일 읽기 가정
        total_tokens += estimate_tokens(content)
        found += 1
    
    conn.close()
    
    elapsed = (time.time() - start) * 1000  # ms
    
    return {
        'time_ms': int(elapsed),
        'tokens': total_tokens,
        'files_read': files_read,
        'found': found
    }

def search_new_way(query):
    """새 방식 (FTS5 + snippet)"""
    start = time.time()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # FTS5 검색 (snippet만)
    results = c.execute("""
    SELECT 
        d.path, 
        snippet(fts_documents, 2, '[', ']', '...', 30) as snippet
    FROM fts_documents
    JOIN documents d ON fts_documents.rowid = d.id
    WHERE fts_documents MATCH ?
    LIMIT 10
    """, (query,)).fetchall()
    
    total_tokens = 0
    found = len(results)
    
    for path, snippet in results:
        # snippet만 읽음 (약 30단어)
        total_tokens += estimate_tokens(snippet) if snippet else 30
    
    conn.close()
    
    elapsed = (time.time() - start) * 1000  # ms
    
    return {
        'time_ms': int(elapsed),
        'tokens': total_tokens,
        'results': found,
        'found': found
    }

def save_performance(query, old_result, new_result, session_tokens=None):
    """성능 기록 저장"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    speedup = old_result['time_ms'] / new_result['time_ms'] if new_result['time_ms'] > 0 else 0
    token_reduction = (1 - new_result['tokens'] / old_result['tokens']) if old_result['tokens'] > 0 else 0
    
    c.execute("""
    INSERT INTO search_performance (
        timestamp, query,
        method_old, time_old_ms, tokens_old, files_read_old, found_old,
        method_new, time_new_ms, tokens_new, results_new, found_new,
        speedup, token_reduction,
        session_tokens
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(datetime.now().timestamp()),
        query,
        'memory_search',
        old_result['time_ms'],
        old_result['tokens'],
        old_result['files_read'],
        old_result['found'],
        'fts',
        new_result['time_ms'],
        new_result['tokens'],
        new_result['results'],
        new_result['found'],
        speedup,
        token_reduction,
        session_tokens
    ))
    
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="검색 성능 비교")
    parser.add_argument("query", help="검색어")
    parser.add_argument("--session-tokens", type=int, help="현재 세션 토큰 사용량")
    parser.add_argument("--silent", action="store_true", help="결과 출력 안 함")
    
    args = parser.parse_args()
    
    if not args.silent:
        print(f"🔍 검색 성능 비교: {args.query}\n")
    
    # 기존 방식
    if not args.silent:
        print("  📖 기존 방식 (memory_search + Read)...")
    old_result = search_old_way(args.query)
    
    # 새 방식
    if not args.silent:
        print("  ⚡ 새 방식 (FTS5 + snippet)...")
    new_result = search_new_way(args.query)
    
    # 성능 비교
    speedup = old_result['time_ms'] / new_result['time_ms'] if new_result['time_ms'] > 0 else 0
    token_reduction = (1 - new_result['tokens'] / old_result['tokens']) if old_result['tokens'] > 0 else 0
    
    if not args.silent:
        print(f"\n  ⏱️  시간:")
        print(f"     기존: {old_result['time_ms']}ms")
        print(f"     새로: {new_result['time_ms']}ms")
        print(f"     → {speedup:.1f}배 빠름")
        
        print(f"\n  🪙 토큰:")
        print(f"     기존: {old_result['tokens']:,}개 ({old_result['files_read']}개 파일)")
        print(f"     새로: {new_result['tokens']:,}개 (snippet)")
        print(f"     → {token_reduction*100:.1f}% 절감")
        
        print(f"\n  📊 결과:")
        print(f"     기존: {old_result['found']}개")
        print(f"     새로: {new_result['found']}개")
    
    # DB 저장
    save_performance(args.query, old_result, new_result, args.session_tokens)
    
    if not args.silent:
        print(f"\n  ✅ 성능 기록 저장 완료")

if __name__ == "__main__":
    main()
