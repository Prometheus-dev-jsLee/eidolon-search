#!/usr/bin/env python3
"""
Eidolon Search v0.1.0 - Human-Like Memory Search

Hybrid search: FTS5 keyword + metadata weighting (emotion, recency, reinforcement)
Based on dual-layer memory architecture.

Usage:
  python scripts/search-v2.py "query" [--limit 10] [--valence 0.5] [--db ./memory.db]
"""

import sys
import os
import json
import math
import sqlite3
import time
import argparse
from pathlib import Path

DB_PATH = os.environ.get('DB_PATH', './memory.db')


def ensure_v2_schema(conn):
    """Ensure v2 schema exists (backward compatible with v0.0.x)"""
    c = conn.cursor()
    
    # Check if memory_meta exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_meta'")
    if not c.fetchone():
        schema_path = Path(__file__).parent.parent / "db" / "schema-v2.sql"
        if schema_path.exists():
            # Only execute non-FTS parts (FTS table already exists)
            schema = schema_path.read_text()
            for statement in schema.split(';'):
                stmt = statement.strip()
                if not stmt:
                    continue
                # Skip only the FTS5 CREATE VIRTUAL TABLE statement
                lines = [l for l in stmt.split('\n') if not l.strip().startswith('--')]
                code_only = ' '.join(lines)
                if 'CREATE VIRTUAL TABLE' in code_only and 'memory_fts' in code_only:
                    continue
                try:
                    c.execute(stmt)
                except sqlite3.OperationalError:
                    pass  # table/index already exists
            conn.commit()
            
            # Backfill metadata for existing FTS entries
            c.execute("SELECT path FROM memory_fts")
            now = time.time()
            for (path,) in c.fetchall():
                c.execute("""
                INSERT OR IGNORE INTO memory_meta (path, created_at, last_recalled, strength)
                VALUES (?, ?, NULL, 1.0)
                """, (path, now))
            conn.commit()
            print("📦 Upgraded to v2 schema")
    
    return conn


def compute_decay(decay_rate, days_elapsed):
    """Ebbinghaus forgetting curve approximation"""
    if days_elapsed <= 0:
        return 1.0
    return max(0.01, decay_rate ** days_elapsed)


def hybrid_search(query, limit=10, current_valence=0.0, db_path=DB_PATH):
    """
    Human-like memory search:
    - FTS5 keyword match (Eidolon's core strength)
    - Emotional affinity
    - Recency weighting
    - Reinforcement boost
    - Decay (forgetting)
    """
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return []
    
    conn = sqlite3.connect(db_path)
    conn = ensure_v2_schema(conn)
    c = conn.cursor()
    
    now = time.time()
    
    # Step 1: FTS5 keyword search (get candidates)
    fts_results = c.execute("""
    SELECT 
        path,
        snippet(memory_fts, 1, '[', ']', '...', 30) as snippet,
        rank
    FROM memory_fts
    WHERE memory_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """, (query, limit * 3)).fetchall()  # Get 3x candidates for re-ranking
    
    if not fts_results:
        conn.close()
        return []
    
    # Step 2: Enrich with metadata and compute human-like scores
    scored_results = []
    
    for path, snippet, fts_rank in fts_results:
        # Get metadata (may not exist for old entries)
        meta = c.execute("""
        SELECT valence, arousal, decay_rate, consolidation, 
               strength, created_at, last_recalled
        FROM memory_meta WHERE path = ?
        """, (path,)).fetchone()
        
        if meta:
            valence, arousal, decay_rate, consolidation, \
                strength, created_at, last_recalled = meta
        else:
            # Defaults for entries without metadata
            valence, arousal, decay_rate = 0.0, 0.5, 0.95
            consolidation, strength = 0, 1.0
            created_at, last_recalled = now, None
        
        # ── Score Components ──
        
        # 1. FTS5 keyword score (normalized, rank is negative)
        keyword_score = 1.0 / (1.0 + abs(fts_rank))
        
        # 2. Emotional affinity
        emotion_score = 1.0 - abs(current_valence - (valence or 0.0))
        
        # 3. Recency weight
        days_ago = (now - (created_at or now)) / 86400
        time_weight = 1.0 / (1.0 + days_ago * 0.1)
        
        # 4. Reinforcement boost
        recall_boost = math.log(1 + (consolidation or 0)) * 0.1
        
        # 5. Current decay state
        days_since_recall = (now - (last_recalled or created_at or now)) / 86400
        current_strength = compute_decay(decay_rate or 0.95, days_since_recall)
        
        # ── Composite Score ──
        final_score = (
            keyword_score    * 0.30
            + emotion_score  * 0.15
            + time_weight    * 0.10
            + recall_boost   * 0.10
            + current_strength * 0.10
            + (keyword_score * current_strength) * 0.25  # FTS × strength interaction
        )
        
        scored_results.append({
            'path': path,
            'snippet': snippet,
            'score': final_score,
            'fts_rank': fts_rank,
            'valence': valence,
            'consolidation': consolidation,
            'strength': current_strength,
            'days_ago': days_ago,
        })
    
    # Step 3: Re-rank by composite score
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Step 4: Log recalls (update consolidation)
    for result in scored_results[:limit]:
        c.execute("""
        INSERT INTO recall_log (path, query, score, recalled_at)
        VALUES (?, ?, ?, ?)
        """, (result['path'], query, result['score'], now))
        
        c.execute("""
        UPDATE memory_meta 
        SET consolidation = consolidation + 1,
            last_recalled = ?,
            strength = ?
        WHERE path = ?
        """, (now, result['strength'], result['path']))
    
    conn.commit()
    conn.close()
    
    return scored_results[:limit]


def main():
    parser = argparse.ArgumentParser(description='Eidolon Search v2 - Human-Like Memory Search')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--limit', type=int, default=10, help='Max results (default: 10)')
    parser.add_argument('--valence', type=float, default=0.0, help='Current emotional state: -1.0 ~ +1.0')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()
    
    results = hybrid_search(args.query, args.limit, args.valence, args.db)
    
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    
    print(f"🧠 Eidolon Search v2 — Human-Like Recall")
    print(f"🔍 Query: {args.query}")
    if args.valence != 0.0:
        mood = "positive" if args.valence > 0 else "negative"
        print(f"💭 Current mood: {mood} ({args.valence:+.1f})")
    print("=" * 60)
    
    if not results:
        print("No memories found.")
    else:
        for i, r in enumerate(results, 1):
            strength_bar = "█" * int(r['strength'] * 10)
            print(f"\n{i}. {r['path']}")
            print(f"   {r['snippet']}")
            print(f"   score={r['score']:.3f}  strength={strength_bar}  "
                  f"recalls={r['consolidation']}  days_ago={r['days_ago']:.0f}")
    
    print(f"\n✅ {len(results)} memories recalled")


if __name__ == "__main__":
    main()
