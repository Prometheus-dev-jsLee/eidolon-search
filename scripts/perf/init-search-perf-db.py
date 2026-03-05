#!/usr/bin/env python3
"""
검색 성능 추적 DB 초기화

테이블:
- search_performance: 검색 성능 비교 기록
"""

import sqlite3
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DB_PATH = WORKSPACE / "documents.db"

def init_search_perf():
    """검색 성능 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # search_performance 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS search_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        query TEXT NOT NULL,
        
        -- 기존 방식 (Read tool + memory_search)
        method_old TEXT DEFAULT 'manual',
        time_old_ms INTEGER,
        tokens_old INTEGER,
        files_read_old INTEGER,
        found_old INTEGER,
        
        -- 새 방식 (search-content.py / embed-vault.py)
        method_new TEXT DEFAULT 'fts',
        time_new_ms INTEGER,
        tokens_new INTEGER,
        results_new INTEGER,
        found_new INTEGER,
        
        -- 비교
        speedup REAL,
        token_reduction REAL,
        accuracy_same INTEGER DEFAULT 1,
        
        -- 메타
        session_tokens INTEGER,
        notes TEXT
    )
    """)
    
    c.execute("""
    CREATE INDEX IF NOT EXISTS idx_search_perf_timestamp 
    ON search_performance(timestamp)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ 검색 성능 테이블 생성 완료: {DB_PATH}")
    print(f"   테이블: search_performance")

if __name__ == "__main__":
    init_search_perf()
