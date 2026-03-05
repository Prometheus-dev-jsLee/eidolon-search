#!/usr/bin/env python3
"""
Alias Dictionary for Eidolon Search

자주 틀리는 고유명사/동의어를 alias로 등록.
검색 시 alias를 원본 키워드로 확장하여 FTS5 검색 정확도 향상.

사용법:
  # alias 추가
  python3 scripts/alias-dict.py add "Phisical" "Physical"
  python3 scripts/alias-dict.py add "인공지능" "AI"
  python3 scripts/alias-dict.py add "차량" "자동차"

  # alias 목록
  python3 scripts/alias-dict.py list

  # 쿼리 확장 (검색 전 사용)
  python3 scripts/alias-dict.py expand "Phisical AI 차량"
  # → "Physical AI 자동차 OR Phisical AI 차량"

  # alias 삭제
  python3 scripts/alias-dict.py remove "Phisical"
"""

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).parent.parent / "db" / "alias.db"

# 기본 alias (자주 틀리는 고유명사 + 동의어)
DEFAULT_ALIASES = {
    # 오타 교정
    "Phisical": "Physical",
    "Qdrant": "Qdrant",
    "Eidelон": "Eidolon",
    "Promethues": "Prometheus",
    "Triangel": "Triangle",
    # 동의어 (한/영)
    "인공지능": "AI",
    "차량": "자동차",
    "로봇": "robot",
    "검색엔진": "search",
    "데이터베이스": "DB",
    "임베딩": "embedding",
    "벡터": "vector",
}


def init_db(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS aliases (
            alias TEXT PRIMARY KEY,
            canonical TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def add_alias(conn, alias: str, canonical: str):
    conn.execute(
        "INSERT OR REPLACE INTO aliases (alias, canonical) VALUES (?, ?)",
        (alias, canonical)
    )
    conn.commit()


def remove_alias(conn, alias: str):
    conn.execute("DELETE FROM aliases WHERE alias = ?", (alias,))
    conn.commit()


def list_aliases(conn):
    cursor = conn.execute("SELECT alias, canonical FROM aliases ORDER BY alias")
    return cursor.fetchall()


def get_alias(conn, word: str):
    cursor = conn.execute(
        "SELECT canonical FROM aliases WHERE alias = ?", (word,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def expand_query(conn, query: str) -> str:
    """쿼리의 각 단어를 alias로 확장"""
    words = query.split()
    expanded = []
    changed = False

    for word in words:
        canonical = get_alias(conn, word)
        if canonical and canonical != word:
            expanded.append(canonical)
            changed = True
        else:
            expanded.append(word)

    if changed:
        return " OR ".join([" ".join(expanded), query])
    return query


def seed_defaults(conn):
    """기본 alias 추가"""
    for alias, canonical in DEFAULT_ALIASES.items():
        add_alias(conn, alias, canonical)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    db_path = DEFAULT_DB

    conn = init_db(db_path)

    if action == "init":
        seed_defaults(conn)
        print(f"기본 alias {len(DEFAULT_ALIASES)}개 추가 완료")

    elif action == "add" and len(sys.argv) >= 4:
        alias, canonical = sys.argv[2], sys.argv[3]
        add_alias(conn, alias, canonical)
        print(f"추가: {alias} → {canonical}")

    elif action == "remove" and len(sys.argv) >= 3:
        alias = sys.argv[2]
        remove_alias(conn, alias)
        print(f"삭제: {alias}")

    elif action == "list":
        aliases = list_aliases(conn)
        if not aliases:
            print("alias 없음. 'init'으로 기본값 추가하세요.")
        for alias, canonical in aliases:
            print(f"  {alias} → {canonical}")
        print(f"\n총 {len(aliases)}개")

    elif action == "expand" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        expanded = expand_query(conn, query)
        print(f"원본:  {query}")
        print(f"확장:  {expanded}")

    else:
        print(__doc__)

    conn.close()
