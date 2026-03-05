#!/usr/bin/env python3
"""
Eidolon Search v0.1.0 - Index Builder with Metadata

Indexes memory files into FTS5 + extracts metadata (emotion, timestamps, tags).
Backward compatible with v0.0.x databases.

Usage:
  python scripts/build-index-v2.py [memory_dir] [db_path]
"""

import sys
import re
import json
import time
import sqlite3
from pathlib import Path
from datetime import datetime


# ── Simple Sentiment Analysis (no dependencies) ──

POSITIVE_WORDS = {
    # Korean
    '좋', '감사', '성공', '완료', '해결', '기쁘', '행복', '축하', '대단',
    '훌륭', '완성', '진전', '발전', '성장', '달성', '만족', '신뢰',
    # English
    'good', 'great', 'success', 'done', 'solved', 'happy', 'complete',
    'progress', 'achieve', 'trust', 'love', 'excellent', 'wonderful',
}

NEGATIVE_WORDS = {
    # Korean
    '실패', '에러', '오류', '문제', '버그', '경고', '위험', '삭제',
    '실수', '후회', '걱정', '불안', '어려', '복잡', '포기',
    # English
    'error', 'fail', 'bug', 'warn', 'danger', 'delete', 'mistake',
    'regret', 'worry', 'difficult', 'complex', 'broken', 'crash',
}


def estimate_valence(text):
    """Simple keyword-based sentiment: -1.0 ~ +1.0"""
    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 2)


def estimate_arousal(text):
    """Simple arousal estimation based on punctuation and emphasis"""
    excl = text.count('!') + text.count('！')
    quest = text.count('?') + text.count('？')
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    
    arousal = min(1.0, (excl * 0.1 + quest * 0.05 + caps_ratio * 2))
    return round(max(0.1, arousal), 2)


def extract_tags(text, path):
    """Extract semantic tags from content and path"""
    tags = []
    
    # From path (date, category)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(path))
    if date_match:
        tags.append(f"date:{date_match.group(1)}")
    
    # From headers
    headers = re.findall(r'^#{1,3}\s+(.+)$', text, re.MULTILINE)
    for h in headers[:5]:
        tag = h.strip().lower()[:30]
        if tag:
            tags.append(f"topic:{tag}")
    
    return tags


def extract_people(text):
    """Extract mentioned people/entities"""
    people = []
    # Korean patterns
    korean_names = re.findall(r'(미라클|프로메테우스|메티)', text)
    people.extend(set(korean_names))
    
    # @mentions
    mentions = re.findall(r'@(\w+)', text)
    people.extend(set(mentions))
    
    return list(set(people))


def extract_timestamp(path_str, file_path):
    """Extract timestamp from path or file mtime"""
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', path_str)
    if date_match:
        y, m, d = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        try:
            return datetime(y, m, d).timestamp()
        except ValueError:
            pass
    
    return file_path.stat().st_mtime


def init_db(db_path):
    """Initialize with v2 schema"""
    conn = sqlite3.connect(db_path)
    
    # Create FTS5 table
    conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
        path,
        content,
        tokenize='porter unicode61 remove_diacritics 2'
    )
    """)
    
    # Create v2 metadata tables
    schema_path = Path(__file__).parent.parent / "db" / "schema-v2.sql"
    if schema_path.exists():
        schema = schema_path.read_text()
        for statement in schema.split(';'):
            stmt = statement.strip()
            if stmt and 'memory_fts' not in stmt:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass
    
    conn.commit()
    return conn


def index_file(conn, file_path, base_dir):
    """Index a file with FTS5 + metadata"""
    try:
        content = file_path.read_text(encoding='utf-8')
        relative_path = str(file_path.relative_to(base_dir))
        c = conn.cursor()
        
        # FTS5 index (same as v0.0.x)
        c.execute("DELETE FROM memory_fts WHERE path = ?", (relative_path,))
        c.execute("INSERT INTO memory_fts (path, content) VALUES (?, ?)",
                  (relative_path, content))
        
        # v2 metadata
        ts = extract_timestamp(relative_path, file_path)
        valence = estimate_valence(content)
        arousal = estimate_arousal(content)
        tags = extract_tags(content, relative_path)
        people = extract_people(content)
        
        c.execute("""
        INSERT OR REPLACE INTO memory_meta 
            (path, created_at, valence, arousal, decay_rate, 
             consolidation, strength, source, tags, social)
        VALUES (?, ?, ?, ?, 0.95, 0, 1.0, 'text', ?, ?)
        """, (relative_path, ts, valence, arousal,
              json.dumps(tags, ensure_ascii=False),
              json.dumps(people, ensure_ascii=False)))
        
        conn.commit()
        return True, valence
    except Exception as e:
        print(f"  ⚠️  Error: {file_path}: {e}")
        return False, 0.0


def main():
    memory_dir = sys.argv[1] if len(sys.argv) > 1 else "./memory"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "./memory.db"
    
    print(f"🧠 Eidolon Search v0.1.0 — Index Builder")
    print(f"📁 Memory dir: {memory_dir}")
    print(f"💾 DB path: {db_path}")
    print("=" * 60)
    
    memory_path = Path(memory_dir)
    if not memory_path.exists():
        print(f"❌ Memory directory not found: {memory_dir}")
        return
    
    files = sorted(memory_path.glob("**/*.md"))
    if not files:
        print("❌ No memory files found")
        return
    
    print(f"📝 Found {len(files)} memory files")
    
    conn = init_db(db_path)
    
    base_dir = memory_path.parent
    success = 0
    total_valence = 0.0
    
    for f in files:
        ok, val = index_file(conn, f, base_dir)
        if ok:
            success += 1
            total_valence += val
    
    conn.close()
    
    avg_valence = total_valence / max(success, 1)
    mood = "positive" if avg_valence > 0.1 else "negative" if avg_valence < -0.1 else "neutral"
    
    print(f"\n📊 Results:")
    print(f"   Indexed: {success}/{len(files)}")
    print(f"   Average valence: {avg_valence:+.2f} ({mood})")
    print(f"   Schema: v2 (FTS5 + metadata)")
    print(f"\n✅ Done")


if __name__ == "__main__":
    main()
