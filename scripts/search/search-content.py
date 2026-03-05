#!/usr/bin/env python3
"""
Vault 전문 검색 (FTS5)

대화 내용을 SQL로 검색:
- 키워드 검색
- 구문 검색 ("exact phrase")
- Boolean 연산 (AND, OR, NOT)
"""

import sqlite3
import argparse
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DB_PATH = WORKSPACE / "documents.db"

def search_content(query, limit=10):
    """FTS5 전문 검색"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # FTS5 쿼리
    results = c.execute("""
    SELECT 
        d.path, 
        d.title,
        snippet(fts_documents, 2, '[', ']', '...', 30) as snippet,
        datetime(d.modified, 'unixepoch', 'localtime') as mod_time,
        rank
    FROM fts_documents
    JOIN documents d ON fts_documents.rowid = d.id
    WHERE fts_documents MATCH ?
    ORDER BY rank
    LIMIT ?
    """, (query, limit)).fetchall()
    
    conn.close()
    return results

def search_by_date_and_keyword(date_pattern, keyword, limit=10):
    """날짜 + 키워드 검색"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    results = c.execute("""
    SELECT 
        path, 
        title,
        substr(content, instr(lower(content), lower(?)) - 50, 150) as snippet,
        datetime(modified, 'unixepoch', 'localtime') as mod_time
    FROM documents
    WHERE path LIKE ?
      AND lower(content) LIKE lower(?)
    ORDER BY modified DESC
    LIMIT ?
    """, (keyword, f"%{date_pattern}%", f"%{keyword}%", limit)).fetchall()
    
    conn.close()
    return results

def main():
    parser = argparse.ArgumentParser(description="Vault 전문 검색 (FTS5)")
    parser.add_argument("query", nargs="?", help="검색어 (FTS5 쿼리)")
    parser.add_argument("-d", "--date", help="날짜 패턴 (예: 2026-03)")
    parser.add_argument("-k", "--keyword", help="날짜 + 키워드 검색 (--date와 함께)")
    parser.add_argument("-l", "--limit", type=int, default=10, help="결과 개수")
    parser.add_argument("--help-fts", action="store_true", help="FTS5 쿼리 문법")
    
    args = parser.parse_args()
    
    if args.help_fts:
        print("""
FTS5 쿼리 문법:

1. 기본 검색
   프로메테우스              - 단어 포함
   
2. 구문 검색
   "Physical AI"            - 정확한 구문
   
3. Boolean
   프로메테우스 AND 미라클    - 둘 다 포함
   AI OR 에이전트            - 하나라도 포함
   프로메테우스 NOT 형제      - 형제 제외
   
4. 접두어
   프로메*                  - 프로메테우스, 프로메시안 등
   
5. 근접 검색
   NEAR(프로메테우스 미라클, 10)  - 10단어 이내
   
6. 컬럼 지정
   title: 프로메테우스       - 제목에서만
   content: "Physical AI"   - 내용에서만

예시:
  python3 search-content.py "Physical AI"
  python3 search-content.py 'NEAR(프로메테우스 의식, 20)'
  python3 search-content.py 'title: 메모리 AND content: 최적화'
  python3 search-content.py -d 2026-03 -k 미라클
        """)
        return
    
    if args.date and args.keyword:
        # 날짜 + 키워드 검색
        print(f"🔍 날짜 + 키워드: {args.date} / {args.keyword}")
        results = search_by_date_and_keyword(args.date, args.keyword, args.limit)
        
        if not results:
            print("   결과 없음")
        else:
            print(f"   {len(results)}개 발견\n")
            for path, title, snippet, mod_time in results:
                print(f"   📄 {title}")
                print(f"      {path} ({mod_time})")
                if snippet:
                    snippet_clean = snippet.replace('\n', ' ').strip()
                    print(f"      ...{snippet_clean}...")
                print()
    
    elif args.query:
        # FTS5 검색
        print(f"🔍 전문 검색: {args.query}")
        results = search_content(args.query, args.limit)
        
        if not results:
            print("   결과 없음")
        else:
            print(f"   {len(results)}개 발견 (관련도 순)\n")
            for path, title, snippet, mod_time, rank in results:
                print(f"   📄 {title}")
                print(f"      {path} ({mod_time})")
                if snippet:
                    snippet_clean = snippet.replace('\n', ' ').strip()
                    print(f"      {snippet_clean}")
                print()
    
    else:
        # 통계
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        docs_with_content = c.execute("""
        SELECT COUNT(*) FROM documents WHERE content IS NOT NULL
        """).fetchone()[0]
        
        total_words = c.execute("""
        SELECT SUM(word_count) FROM documents WHERE content IS NOT NULL
        """).fetchone()[0] or 0
        
        print("📊 전문 검색 통계:")
        print(f"   콘텐츠 저장: {docs_with_content}개 문서")
        print(f"   총 단어: {total_words:,}개")
        print(f"\n사용법:")
        print(f"   python3 search-content.py '검색어'")
        print(f"   python3 search-content.py --help-fts")
        
        conn.close()

if __name__ == "__main__":
    main()
