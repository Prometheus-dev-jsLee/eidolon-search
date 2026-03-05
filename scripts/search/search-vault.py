#!/usr/bin/env python3
"""
Vault 통합 검색 스크립트

3가지 검색 방식:
1. 텍스트 검색 (RDB - 제목, 경로)
2. 태그 검색 (RDB - 태그 필터)
3. 시맨틱 검색 (Qdrant - 의미 기반)
"""

import sqlite3
import argparse
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DB_PATH = WORKSPACE / "documents.db"
VAULT_PATH = WORKSPACE / "vault"

def search_text(query, limit=10):
    """텍스트 검색 (제목, 경로)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    results = c.execute("""
    SELECT path, title, word_count, datetime(modified, 'unixepoch', 'localtime') as mod_time
    FROM documents
    WHERE title LIKE ? OR path LIKE ?
    ORDER BY modified DESC
    LIMIT ?
    """, (f"%{query}%", f"%{query}%", limit)).fetchall()
    
    conn.close()
    return results

def search_by_tag(tag, limit=10):
    """태그 검색"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    results = c.execute("""
    SELECT d.path, d.title, d.word_count, datetime(d.modified, 'unixepoch', 'localtime') as mod_time
    FROM documents d
    JOIN document_tags dt ON d.id = dt.document_id
    JOIN tags t ON dt.tag_id = t.id
    WHERE t.name = ?
    ORDER BY d.modified DESC
    LIMIT ?
    """, (tag, limit)).fetchall()
    
    conn.close()
    return results

def get_document_tags(doc_path):
    """문서의 태그 목록"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    tags = c.execute("""
    SELECT t.name
    FROM tags t
    JOIN document_tags dt ON t.id = dt.tag_id
    JOIN documents d ON dt.document_id = d.id
    WHERE d.path = ?
    """, (doc_path,)).fetchall()
    
    conn.close()
    return [t[0] for t in tags]

def get_backlinks(doc_path):
    """백링크 (이 문서를 참조하는 문서들)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 경로 정규화
    if not doc_path.endswith('.md'):
        doc_path = f"{doc_path}.md"
    
    backlinks = c.execute("""
    SELECT d.path, d.title
    FROM documents d
    JOIN links l ON d.id = l.source_id
    WHERE l.target_path LIKE ?
    """, (f"%{doc_path}%",)).fetchall()
    
    conn.close()
    return backlinks

def main():
    parser = argparse.ArgumentParser(description="Vault 통합 검색")
    parser.add_argument("query", nargs="?", help="검색어")
    parser.add_argument("-t", "--tag", help="태그 검색")
    parser.add_argument("-b", "--backlinks", help="백링크 조회 (문서 경로)")
    parser.add_argument("-l", "--limit", type=int, default=10, help="결과 개수 (기본: 10)")
    
    args = parser.parse_args()
    
    if args.backlinks:
        # 백링크 조회
        print(f"🔗 백링크: {args.backlinks}")
        backlinks = get_backlinks(args.backlinks)
        if not backlinks:
            print("   백링크 없음")
        else:
            for path, title in backlinks:
                print(f"   ← {title}")
                print(f"      {path}")
    
    elif args.tag:
        # 태그 검색
        print(f"🏷️  태그 검색: #{args.tag}")
        results = search_by_tag(args.tag, args.limit)
        
        if not results:
            print("   결과 없음")
        else:
            print(f"   {len(results)}개 문서 발견")
            for path, title, wc, mod_time in results:
                tags = get_document_tags(path)
                print(f"\n   📄 {title}")
                print(f"      {path}")
                print(f"      {wc} words | {mod_time}")
                print(f"      태그: {', '.join(['#' + t for t in tags])}")
    
    elif args.query:
        # 텍스트 검색
        print(f"🔍 텍스트 검색: {args.query}")
        results = search_text(args.query, args.limit)
        
        if not results:
            print("   결과 없음")
        else:
            print(f"   {len(results)}개 문서 발견")
            for path, title, wc, mod_time in results:
                tags = get_document_tags(path)
                print(f"\n   📄 {title}")
                print(f"      {path}")
                print(f"      {wc} words | {mod_time}")
                if tags:
                    print(f"      태그: {', '.join(['#' + t for t in tags])}")
    
    else:
        # 통계
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        docs = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        tags = c.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        links = c.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        
        print("📊 Vault 통계:")
        print(f"   문서: {docs}개")
        print(f"   태그: {tags}개")
        print(f"   링크: {links}개")
        
        print("\n🏷️  상위 태그:")
        top_tags = c.execute("""
        SELECT tags.name, COUNT(*) as cnt 
        FROM tags 
        JOIN document_tags ON tags.id = document_tags.tag_id 
        GROUP BY tags.name 
        ORDER BY cnt DESC 
        LIMIT 10
        """).fetchall()
        
        for tag, cnt in top_tags:
            print(f"   #{tag}: {cnt}개")
        
        conn.close()

if __name__ == "__main__":
    main()
