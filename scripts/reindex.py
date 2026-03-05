#!/usr/bin/env python3
"""
Eidolon Search - Memory Re-indexing (Unconscious Re-interpretation)

논문 Section 06의 핵심 개념:
"오늘의 새 경험이 기존 기억의 의미를 바꾼다"
"그때 그 사람이 왜 그랬는지 이제 이해가 돼"

기억의 원본(페이로드)은 변경하지 않지만, 메타데이터(해석)를 갱신한다.
- 새로 추가된 기억과 의미적으로 연결된 기존 기억을 찾아 link 생성
- 오래된 기억의 tags를 새 맥락으로 보강
- 감정 가중치(valence)를 현재 맥락에 따라 미세 조정

Usage:
  python scripts/reindex.py [--db ./memory.db] [--window 24] [--dry-run]
"""

import os
import sys
import json
import time
import sqlite3
import argparse
import re
from pathlib import Path
from collections import Counter

DB_PATH = os.environ.get('DB_PATH', './memory.db')


def extract_keywords(text, min_len=2):
    """텍스트에서 의미 있는 키워드 추출 (간단한 빈도 기반)"""
    # 한글/영문 단어 추출
    words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', text.lower())
    # 불용어 제거
    stopwords = {'있다', '없다', '하다', '되다', '이다', '그리고', '하지만', '때문',
                 'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was'}
    return [w for w in words if w not in stopwords and len(w) >= min_len]


def find_semantic_neighbors(conn, path, content_keywords, limit=10):
    """FTS5로 의미적으로 가까운 기억 검색"""
    if not content_keywords:
        return []
    
    # OR 검색으로 후보 찾기
    query = ' OR '.join(content_keywords[:10])
    try:
        results = conn.execute("""
        SELECT path, snippet(memory_fts, 1, '', '', '', 20) as snippet, rank
        FROM memory_fts
        WHERE memory_fts MATCH ? AND path != ?
        ORDER BY rank
        LIMIT ?
        """, (query, path, limit)).fetchall()
        return results
    except sqlite3.OperationalError:
        return []


def reindex(db_path=DB_PATH, window_hours=24, dry_run=False, verbose=False):
    """
    새 기억이 기존 기억과 어떻게 연결되는지 발견하고 기록한다.
    
    1. 최근 window_hours 내 추가된 새 기억 수집
    2. 각 새 기억의 키워드로 기존 기억 검색
    3. 의미적 연결(memory_links) 생성
    4. 기존 기억의 tags 보강
    """
    if not Path(db_path).exists():
        print(f"DB not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    now = time.time()
    window_start = now - (window_hours * 3600)
    
    stats = {
        'new_memories': 0,
        'links_created': 0,
        'tags_updated': 0,
    }
    
    # 1. 최근 추가된 기억 수집
    new_memories = c.execute("""
    SELECT m.path, f.content
    FROM memory_meta m
    JOIN memory_fts f ON m.path = f.path
    WHERE m.created_at > ?
    ORDER BY m.created_at DESC
    """, (window_start,)).fetchall()
    
    stats['new_memories'] = len(new_memories)
    
    if verbose:
        print(f"새 기억 {len(new_memories)}개 발견 (최근 {window_hours}시간)")
    
    for new_path, new_content in new_memories:
        keywords = extract_keywords(new_content)
        if not keywords:
            continue
        
        # 2. 기존 기억에서 의미적 이웃 검색
        neighbors = find_semantic_neighbors(conn, new_path, keywords)
        
        for old_path, snippet, rank in neighbors:
            # 3. memory_links 생성
            if not dry_run:
                c.execute("""
                INSERT OR IGNORE INTO memory_links 
                    (source_path, target_path, link_type, strength, created_at)
                VALUES (?, ?, 'semantic', ?, ?)
                """, (new_path, old_path, min(1.0, 1.0 / (1.0 + abs(rank))), now))
                
                # 역방향 링크도 (기억은 양방향)
                c.execute("""
                INSERT OR IGNORE INTO memory_links 
                    (source_path, target_path, link_type, strength, created_at)
                VALUES (?, ?, 'semantic', ?, ?)
                """, (old_path, new_path, min(1.0, 1.0 / (1.0 + abs(rank))), now))
            
            stats['links_created'] += 1
            
            if verbose:
                print(f"  링크: {new_path} <-> {old_path} (강도: {1.0/(1.0+abs(rank)):.3f})")
        
        # 4. 키워드를 기존 기억의 tags에 보강
        top_keywords = [k for k, _ in Counter(keywords).most_common(5)]
        
        for old_path, _, _ in neighbors[:3]:
            existing_tags = c.execute(
                "SELECT tags FROM memory_meta WHERE path = ?", (old_path,)
            ).fetchone()
            
            if existing_tags and existing_tags[0]:
                try:
                    tags = json.loads(existing_tags[0])
                except (json.JSONDecodeError, TypeError):
                    tags = []
            else:
                tags = []
            
            new_tags = list(set(tags + top_keywords))[:20]  # 최대 20개
            
            if new_tags != tags:
                if not dry_run:
                    c.execute(
                        "UPDATE memory_meta SET tags = ? WHERE path = ?",
                        (json.dumps(new_tags, ensure_ascii=False), old_path)
                    )
                stats['tags_updated'] += 1
    
    if not dry_run:
        conn.commit()
    conn.close()
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Eidolon Memory Re-indexing — 새 경험이 기존 기억의 의미를 갱신'
    )
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--window', type=int, default=24, help='Hours to look back (default: 24)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    stats = reindex(args.db, args.window, args.dry_run, args.verbose)
    
    if stats:
        mode = "[DRY RUN] " if args.dry_run else ""
        print(f"\n{mode}재인덱싱 완료:")
        print(f"  새 기억: {stats['new_memories']}개")
        print(f"  링크 생성: {stats['links_created']}개")
        print(f"  태그 보강: {stats['tags_updated']}건")


if __name__ == "__main__":
    main()
