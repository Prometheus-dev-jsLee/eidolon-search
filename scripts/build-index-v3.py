#!/usr/bin/env python3
"""
Eidolon Search v0.2.0 - Index Builder with Multimodal Support

Indexes memory files into:
  - FTS5 (keyword search)
  - memory_meta (emotional & temporal metadata)
  - memory_payload (multimodal content references)
  - emotion_tags (auto-tagged emotional analysis)

Backward compatible: runs v1 schema first, then v2/v3 extensions.

Usage:
  python scripts/build-index-v3.py [memory_dir] [db_path]
  python scripts/build-index-v3.py --with-audio /path/to/voice-memos/
"""

import sys
import os
import re
import json
import time
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent


# ── Schema ──

SCHEMA_V1 = """
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    path, content,
    tokenize='porter unicode61 remove_diacritics 2'
);
"""

SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS memory_meta (
    path TEXT PRIMARY KEY,
    created_at REAL, last_recalled REAL,
    valence REAL DEFAULT 0.0, arousal REAL DEFAULT 0.5,
    decay_rate REAL DEFAULT 0.95, consolidation INTEGER DEFAULT 0,
    strength REAL DEFAULT 1.0,
    source TEXT DEFAULT 'text',
    tags TEXT DEFAULT '[]', social TEXT DEFAULT '[]',
    vector BLOB DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS recall_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL, query TEXT NOT NULL,
    score REAL, recalled_at REAL NOT NULL,
    context TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS memory_links (
    source_path TEXT NOT NULL, target_path TEXT NOT NULL,
    link_type TEXT DEFAULT 'semantic', strength REAL DEFAULT 1.0,
    created_at REAL,
    PRIMARY KEY (source_path, target_path, link_type)
);
"""

SCHEMA_V3 = """
CREATE TABLE IF NOT EXISTS memory_payload (
    path TEXT PRIMARY KEY,
    text_content TEXT NOT NULL,
    text_summary TEXT DEFAULT NULL,
    audio_path TEXT DEFAULT NULL, audio_format TEXT DEFAULT NULL,
    audio_duration_s REAL DEFAULT NULL,
    image_path TEXT DEFAULT NULL, image_caption TEXT DEFAULT NULL,
    video_path TEXT DEFAULT NULL, video_duration_s REAL DEFAULT NULL,
    modalities TEXT DEFAULT '["text"]',
    byte_size INTEGER DEFAULT 0,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS emotion_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    valence REAL NOT NULL, arousal REAL NOT NULL,
    emotions TEXT DEFAULT '[]',
    method TEXT DEFAULT 'keyword', confidence REAL DEFAULT 0.5,
    tagged_at REAL NOT NULL, context TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS sensory_anchors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    anchor_type TEXT NOT NULL, anchor_value TEXT NOT NULL,
    strength REAL DEFAULT 1.0, created_at REAL
);

CREATE INDEX IF NOT EXISTS idx_payload_modalities ON memory_payload(modalities);
CREATE INDEX IF NOT EXISTS idx_emotion_path ON emotion_tags(path);
CREATE INDEX IF NOT EXISTS idx_anchor_path ON sensory_anchors(path);
"""


def init_db(db_path):
    """Initialize database with all schema versions"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # v1: FTS5
    for stmt in SCHEMA_V1.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            try:
                c.execute(stmt)
            except sqlite3.OperationalError:
                pass  # FTS table already exists
    
    # v2: metadata
    for stmt in SCHEMA_V2.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            try:
                c.execute(stmt)
            except sqlite3.OperationalError:
                pass
    
    # v3: multimodal + emotion
    for stmt in SCHEMA_V3.strip().split(';'):
        stmt = stmt.strip()
        if stmt:
            try:
                c.execute(stmt)
            except sqlite3.OperationalError:
                pass
    
    conn.commit()
    return conn


# ── Emotion Analysis (imported from emotion-tagger.py) ──

POSITIVE_WORDS = {
    '좋', '감사', '성공', '완료', '해결', '기쁘', '행복', '축하', '대단',
    '훌륭', '완성', '진전', '발전', '성장', '달성', '만족', '신뢰', '설레',
    'good', 'great', 'success', 'done', 'solved', 'happy', 'complete',
    'progress', 'achieve', 'trust', 'love', 'excellent', 'exciting',
}

NEGATIVE_WORDS = {
    '실패', '문제', '에러', '오류', '안됨', '막힘', '짜증', '답답', '걱정',
    '불안', '위험', '주의', '경고', '슬프', '실망', '후회',
    'fail', 'error', 'bug', 'stuck', 'broken', 'worry', 'risk', 'sad',
}


def quick_sentiment(text):
    """Fast valence/arousal estimation"""
    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    total = pos + neg
    if total == 0:
        return 0.0, 0.3
    valence = (pos - neg) / total
    arousal = min(1.0, 0.3 + total * 0.05)
    return round(valence, 3), round(arousal, 3)


# ── Social Context Extraction ──

KNOWN_NAMES = ['미라클', 'Miracle', '프로메테우스', 'Prometheus']


def extract_social(text):
    """Extract mentioned people"""
    found = [name for name in KNOWN_NAMES if name in text]
    return json.dumps(found, ensure_ascii=False)


# ── Sensory Anchor Detection ──

def extract_anchors(text, path):
    """Find potential sensory anchors (phrases, quotes, key moments)"""
    anchors = []
    
    # Quoted text (memorable phrases)
    quotes = re.findall(r'[""「]([^""」]{5,80})[""」]', text)
    for q in quotes[:3]:
        anchors.append(('phrase', q))
    
    # Bold/emphasized text in markdown
    bolds = re.findall(r'\*\*([^*]{3,50})\*\*', text)
    for b in bolds[:3]:
        anchors.append(('phrase', b))
    
    # Date-specific events (strong temporal anchors)
    dates = re.findall(r'(2026-\d{2}-\d{2})', text)
    for d in dates[:2]:
        anchors.append(('temporal', d))
    
    return anchors


# ── File Discovery ──

def find_memory_files(memory_dir, audio_dir=None):
    """Find all indexable files"""
    files = []
    memory_path = Path(memory_dir)
    
    if not memory_path.exists():
        return files
    
    # Markdown files
    for md in sorted(memory_path.rglob('*.md')):
        entry = {
            'path': str(md.relative_to(memory_path.parent)),
            'abs_path': str(md),
            'modalities': ['text'],
        }
        files.append(entry)
    
    # Audio files (if audio_dir provided)
    if audio_dir:
        audio_path = Path(audio_dir)
        if audio_path.exists():
            for ext in ['*.wav', '*.mp3', '*.ogg', '*.m4a']:
                for af in sorted(audio_path.rglob(ext)):
                    # Try to match with a text file
                    stem = af.stem
                    entry = {
                        'path': f'audio/{af.name}',
                        'abs_path': str(af),
                        'modalities': ['audio'],
                        'audio_path': str(af),
                        'audio_format': af.suffix[1:],
                    }
                    files.append(entry)
    
    return files


def index_file(conn, entry):
    """Index a single file into all tables"""
    c = conn.cursor()
    path = entry['path']
    now = time.time()
    
    # Read text content
    abs_path = entry['abs_path']
    try:
        if abs_path.endswith('.md') or abs_path.endswith('.txt'):
            text = Path(abs_path).read_text(encoding='utf-8')
        else:
            text = f"[{entry.get('modalities', ['unknown'])[0]} file: {path}]"
    except Exception as e:
        print(f"  ⚠️ Skip {path}: {e}")
        return False
    
    if not text.strip():
        return False
    
    # Get file created time
    try:
        stat = Path(abs_path).stat()
        created = stat.st_mtime
    except:
        created = now
    
    # Sentiment
    valence, arousal = quick_sentiment(text)
    
    # Social context
    social = extract_social(text)
    
    # Sensory anchors
    anchors = extract_anchors(text, path)
    
    # Modalities
    modalities = entry.get('modalities', ['text'])
    
    # ── Insert into FTS5 ──
    try:
        c.execute("DELETE FROM memory_fts WHERE path = ?", (path,))
        c.execute("INSERT INTO memory_fts (path, content) VALUES (?, ?)", (path, text))
    except Exception as e:
        print(f"  ⚠️ FTS error {path}: {e}")
    
    # ── Insert into memory_meta ──
    c.execute("""
        INSERT OR REPLACE INTO memory_meta 
        (path, created_at, valence, arousal, decay_rate, consolidation, strength, 
         source, tags, social)
        VALUES (?, ?, ?, ?, 0.95, 0, 1.0, ?, '[]', ?)
    """, (path, created, valence, arousal, 
          'mixed' if len(modalities) > 1 else modalities[0], social))
    
    # ── Insert into memory_payload ──
    byte_size = len(text.encode('utf-8'))
    c.execute("""
        INSERT OR REPLACE INTO memory_payload
        (path, text_content, audio_path, audio_format, image_path, 
         modalities, byte_size, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (path, text, 
          entry.get('audio_path'), entry.get('audio_format'),
          entry.get('image_path'),
          json.dumps(modalities), byte_size, created))
    
    # ── Insert sensory anchors ──
    for anchor_type, anchor_value in anchors:
        c.execute("""
            INSERT OR IGNORE INTO sensory_anchors (path, anchor_type, anchor_value, strength, created_at)
            VALUES (?, ?, ?, 1.0, ?)
        """, (path, anchor_type, anchor_value, now))
    
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Eidolon v0.2.0 Index Builder')
    parser.add_argument('memory_dir', nargs='?', default=str(WORKSPACE.parent / 'memory'))
    parser.add_argument('db_path', nargs='?', default=str(WORKSPACE / 'memory.db'))
    parser.add_argument('--with-audio', default=None, help='Audio directory to index')
    parser.add_argument('--rebuild', action='store_true', help='Drop and rebuild all')
    args = parser.parse_args()
    
    print(f"📚 Eidolon v0.2.0 Index Builder")
    print(f"   Memory: {args.memory_dir}")
    print(f"   DB: {args.db_path}")
    
    conn = init_db(args.db_path)
    
    if args.rebuild:
        c = conn.cursor()
        for table in ['memory_fts', 'memory_meta', 'memory_payload', 
                       'emotion_tags', 'sensory_anchors']:
            try:
                c.execute(f"DELETE FROM {table}")
            except:
                pass
        conn.commit()
        print("   Rebuilt all tables")
    
    files = find_memory_files(args.memory_dir, args.with_audio)
    print(f"   Found {len(files)} files")
    
    indexed = 0
    for entry in files:
        if index_file(conn, entry):
            indexed += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n   ✅ Indexed {indexed}/{len(files)} files")
    print(f"   Schema: v3 (FTS5 + meta + payload + emotion + anchors)")


if __name__ == '__main__':
    main()
