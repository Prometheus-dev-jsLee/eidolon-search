#!/usr/bin/env python3
"""
Eidolon Search v0.2.0 - Emotion Auto-Tagger

Analyzes memory entries and assigns emotional metadata.
Two methods:
  1. Keyword-based (fast, no API cost)
  2. LLM-based (accurate, requires API key)

Based on the paper: "감정 차원(valence)의 값이 회상 시마다 현재 기분 상태에 의해 덮어써지는 현상"

Usage:
  python scripts/emotion-tagger.py [--method keyword|llm] [--db memory.db]
  python scripts/emotion-tagger.py --path "memory/2026-03-05.md" --method llm
"""

import sys
import os
import json
import re
import time
import sqlite3
import argparse
from pathlib import Path

DB_PATH = os.environ.get('DB_PATH', str(Path(__file__).parent.parent / 'memory.db'))


# ── Keyword-based Emotion Analysis ──

EMOTION_LEXICON = {
    'joy': {
        'words': ['기쁘', '행복', '좋', '감사', '축하', '훌륭', '대단', '신나', '즐거',
                  'happy', 'joy', 'great', 'wonderful', 'excellent', 'celebrate', 'love'],
        'valence': 0.8, 'arousal': 0.6
    },
    'satisfaction': {
        'words': ['완료', '성공', '해결', '달성', '완성', '진전', '발전', '성장', '만족',
                  'done', 'success', 'solved', 'complete', 'progress', 'achieve', 'satisfied'],
        'valence': 0.6, 'arousal': 0.4
    },
    'gratitude': {
        'words': ['고맙', '감사', '신뢰', '믿', '부탁',
                  'thank', 'grateful', 'trust', 'appreciate'],
        'valence': 0.7, 'arousal': 0.3
    },
    'excitement': {
        'words': ['설레', '흥미', '놀라', '기대', '와', '대박',
                  'exciting', 'wow', 'amazing', 'incredible', 'breakthrough'],
        'valence': 0.7, 'arousal': 0.9
    },
    'frustration': {
        'words': ['실패', '문제', '에러', '오류', '안됨', '막힘', '짜증', '답답',
                  'fail', 'error', 'bug', 'stuck', 'broken', 'frustrated'],
        'valence': -0.5, 'arousal': 0.6
    },
    'worry': {
        'words': ['걱정', '불안', '위험', '주의', '경고', '조심',
                  'worry', 'risk', 'danger', 'warning', 'careful', 'concern'],
        'valence': -0.3, 'arousal': 0.5
    },
    'sadness': {
        'words': ['슬프', '아쉬', '실망', '후회', '잃', '놓',
                  'sad', 'miss', 'lost', 'regret', 'disappoint'],
        'valence': -0.6, 'arousal': 0.2
    },
    'determination': {
        'words': ['결심', '각오', '반드시', '꼭', '의지', '도전', '포기하지',
                  'must', 'will', 'determined', 'commit', 'never give up'],
        'valence': 0.4, 'arousal': 0.7
    },
    'reflection': {
        'words': ['깨달', '발견', '통찰', '교훈', '배움', '이해', '알게',
                  'realize', 'insight', 'learn', 'understand', 'discover'],
        'valence': 0.3, 'arousal': 0.3
    },
    'neutral': {
        'words': [],
        'valence': 0.0, 'arousal': 0.3
    }
}


def keyword_analyze(text):
    """Fast keyword-based emotion analysis"""
    text_lower = text.lower()
    scores = {}
    
    for emotion, data in EMOTION_LEXICON.items():
        if emotion == 'neutral':
            continue
        count = sum(1 for word in data['words'] if word in text_lower)
        if count > 0:
            scores[emotion] = count
    
    if not scores:
        return {
            'valence': 0.0,
            'arousal': 0.3,
            'emotions': ['neutral'],
            'confidence': 0.3,
            'method': 'keyword'
        }
    
    # Weighted average by frequency
    total = sum(scores.values())
    valence = sum(scores[e] * EMOTION_LEXICON[e]['valence'] for e in scores) / total
    arousal = sum(scores[e] * EMOTION_LEXICON[e]['arousal'] for e in scores) / total
    
    # Top 3 emotions
    top_emotions = sorted(scores, key=scores.get, reverse=True)[:3]
    
    # Confidence based on total hits and variety
    confidence = min(0.8, 0.3 + (total * 0.05) + (len(scores) * 0.05))
    
    return {
        'valence': round(max(-1.0, min(1.0, valence)), 3),
        'arousal': round(max(0.0, min(1.0, arousal)), 3),
        'emotions': top_emotions,
        'confidence': round(confidence, 3),
        'method': 'keyword'
    }


def update_db(db_path, path, result):
    """Update memory_meta and emotion_tags"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    now = time.time()
    
    # Update memory_meta
    c.execute("""
        UPDATE memory_meta 
        SET valence = ?, arousal = ?
        WHERE path = ?
    """, (result['valence'], result['arousal'], path))
    
    # Insert emotion tag log
    try:
        c.execute("""
            INSERT INTO emotion_tags (path, valence, arousal, emotions, method, confidence, tagged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (path, result['valence'], result['arousal'], 
              json.dumps(result['emotions']), result['method'], 
              result['confidence'], now))
    except sqlite3.OperationalError:
        # Table might not exist yet, create it
        c.execute("""
            CREATE TABLE IF NOT EXISTS emotion_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                valence REAL NOT NULL,
                arousal REAL NOT NULL,
                emotions TEXT DEFAULT '[]',
                method TEXT DEFAULT 'keyword',
                confidence REAL DEFAULT 0.5,
                tagged_at REAL NOT NULL,
                context TEXT DEFAULT NULL
            )
        """)
        c.execute("""
            INSERT INTO emotion_tags (path, valence, arousal, emotions, method, confidence, tagged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (path, result['valence'], result['arousal'],
              json.dumps(result['emotions']), result['method'],
              result['confidence'], now))
    
    conn.commit()
    conn.close()


def tag_all(db_path, method='keyword', target_path=None):
    """Tag all or specific memory entries"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if target_path:
        c.execute("SELECT path, content FROM memory_fts WHERE path = ?", (target_path,))
    else:
        c.execute("SELECT path, content FROM memory_fts")
    
    rows = c.fetchall()
    conn.close()
    
    results = []
    for path, content in rows:
        if method == 'keyword':
            result = keyword_analyze(content)
        else:
            # LLM method (placeholder for future)
            result = keyword_analyze(content)
            result['method'] = 'keyword_fallback'
        
        result['path'] = path
        results.append(result)
        
        # Update DB
        update_db(db_path, path, result)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Eidolon Emotion Auto-Tagger')
    parser.add_argument('--method', choices=['keyword', 'llm'], default='keyword')
    parser.add_argument('--path', default=None, help='Tag specific memory path')
    parser.add_argument('--db', default=DB_PATH)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--dry-run', action='store_true', help='Analyze without writing')
    args = parser.parse_args()
    
    if not Path(args.db).exists():
        print(f"❌ Database not found: {args.db}")
        sys.exit(1)
    
    print(f"🏷️  Emotion tagger (method={args.method})")
    
    if args.dry_run:
        conn = sqlite3.connect(args.db)
        c = conn.cursor()
        if args.path:
            c.execute("SELECT path, content FROM memory_fts WHERE path = ?", (args.path,))
        else:
            c.execute("SELECT path, content FROM memory_fts LIMIT 20")
        rows = c.fetchall()
        conn.close()
        
        for path, content in rows:
            result = keyword_analyze(content)
            emotions_str = ', '.join(result['emotions'])
            print(f"  {path}: v={result['valence']:+.2f} a={result['arousal']:.2f} [{emotions_str}] (conf={result['confidence']})")
        return
    
    results = tag_all(args.db, method=args.method, target_path=args.path)
    
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"  Tagged {len(results)} memories")
        
        # Summary
        pos = sum(1 for r in results if r['valence'] > 0.1)
        neg = sum(1 for r in results if r['valence'] < -0.1)
        neu = len(results) - pos - neg
        avg_v = sum(r['valence'] for r in results) / max(1, len(results))
        avg_a = sum(r['arousal'] for r in results) / max(1, len(results))
        
        print(f"\n  Summary:")
        print(f"    Positive: {pos} | Neutral: {neu} | Negative: {neg}")
        print(f"    Avg valence: {avg_v:+.3f} | Avg arousal: {avg_a:.3f}")
        
        # Top emotions
        all_emotions = {}
        for r in results:
            for e in r['emotions']:
                all_emotions[e] = all_emotions.get(e, 0) + 1
        top = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"    Top emotions: {', '.join(f'{e}({c})' for e,c in top)}")


if __name__ == '__main__':
    main()
