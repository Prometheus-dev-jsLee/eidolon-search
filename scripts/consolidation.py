#!/usr/bin/env python3
"""
Eidolon Search - Memory Consolidation (Unconscious Background Process)

Equivalent to sleep consolidation in human memory:
1. Decay: unretrieved memories fade (Ebbinghaus curve)
2. Reinforce: frequently recalled memories strengthen
3. Emotional drift: current context slowly shifts old valence
4. Prune: memories below threshold are soft-deleted

Run as cron/heartbeat job:
  python scripts/consolidation.py [--db ./memory.db] [--dry-run]
"""

import os
import sys
import json
import math
import time
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.environ.get('DB_PATH', './memory.db')


def consolidate(db_path=DB_PATH, dry_run=False, verbose=False):
    """
    Run one consolidation cycle.
    Call this from cron, heartbeat, or manually.
    """
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    now = time.time()
    stats = {
        'decayed': 0,
        'reinforced': 0,
        'pruned': 0,
        'total': 0,
    }
    
    # Get all memories with metadata
    memories = c.execute("""
    SELECT path, decay_rate, consolidation, strength, 
           created_at, last_recalled, valence
    FROM memory_meta
    """).fetchall()
    
    stats['total'] = len(memories)
    
    for path, decay_rate, consolidation, strength, created_at, last_recalled, valence in memories:
        decay_rate = decay_rate or 0.95
        consolidation = consolidation or 0
        created_at = created_at or now
        
        # ── 1. Decay: Ebbinghaus forgetting curve ──
        last_active = last_recalled or created_at
        days_since = (now - last_active) / 86400
        
        if days_since > 7:
            # Decay rate applied per week of inactivity
            weeks = days_since / 7
            new_strength = max(0.01, (decay_rate ** weeks))
            
            # But highly consolidated memories resist decay
            resistance = min(1.0, math.log(1 + consolidation) * 0.2)
            new_strength = new_strength + (1.0 - new_strength) * resistance
            new_strength = min(1.0, new_strength)
            
            if abs(new_strength - (strength or 1.0)) > 0.001:
                if not dry_run:
                    c.execute("""
                    UPDATE memory_meta SET strength = ? WHERE path = ?
                    """, (new_strength, path))
                stats['decayed'] += 1
                if verbose:
                    print(f"  📉 {path}: strength {strength:.3f} → {new_strength:.3f} "
                          f"(inactive {days_since:.0f} days, recalls={consolidation})")
        
        # ── 2. Reinforce: recently recalled memories get boost ──
        if last_recalled and (now - last_recalled) < 86400 * 3:  # recalled in last 3 days
            boost = min(0.05, consolidation * 0.005)
            new_strength = min(1.0, (strength or 0.5) + boost)
            if boost > 0.001:
                if not dry_run:
                    c.execute("""
                    UPDATE memory_meta SET strength = ? WHERE path = ?
                    """, (new_strength, path))
                stats['reinforced'] += 1
                if verbose:
                    print(f"  📈 {path}: reinforced +{boost:.3f} (recalls={consolidation})")
        
        # ── 3. Emotional Drift (Rosy Retrospection) ──
        # 논문 Section 06: 현재 감정 상태가 과거 기억의 valence를 미세하게 조정
        # "추억 미화"의 계산론적 구현: 매 주기마다 alpha=0.05로 중립 방향 이동
        # 자주 회상된 기억은 더 강하게 드리프트 (회상 시 현재 기분 반영)
        if valence is not None and days_since > 30:  # 30일 이상 된 기억만
            # 기본: 시간이 지나면 중립(0.0) 방향으로 서서히 이동
            # 긍정 기억은 약간 더 긍정으로 (survivorship bias), 부정은 중립으로
            if valence < 0:
                alpha = 0.03  # 부정 기억은 빠르게 중화
            else:
                alpha = 0.01  # 긍정 기억은 천천히 변화
            
            new_valence = valence * (1.0 - alpha)  # 중립(0) 방향으로 수렴
            
            if abs(new_valence - valence) > 0.001:
                if not dry_run:
                    c.execute("""
                    UPDATE memory_meta SET valence = ? WHERE path = ?
                    """, (new_valence, path))
                if verbose:
                    print(f"  💭 {path}: valence {valence:+.3f} → {new_valence:+.3f} (emotional drift)")
        
        # ── 4. Prune: memories below threshold ──
        if (strength or 1.0) < 0.05 and consolidation == 0:
            stats['pruned'] += 1
            if verbose:
                print(f"  🗑️  {path}: strength={strength:.3f} (candidate for pruning)")
            # Note: we don't actually delete — just flag for review
            # Actual deletion requires explicit user action
    
    if not dry_run:
        conn.commit()
    conn.close()
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Eidolon Memory Consolidation')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show per-memory details')
    parser.add_argument('--json', action='store_true', help='Output stats as JSON')
    args = parser.parse_args()
    
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if not args.json:
        print(f"🌙 Eidolon Memory Consolidation — {ts}")
        if args.dry_run:
            print("   (dry run — no changes applied)")
        print("=" * 50)
    
    stats = consolidate(args.db, args.dry_run, args.verbose)
    
    if stats is None:
        return
    
    if args.json:
        print(json.dumps(stats))
    else:
        print(f"\n📊 Results:")
        print(f"   Total memories: {stats['total']}")
        print(f"   Decayed:        {stats['decayed']}")
        print(f"   Reinforced:     {stats['reinforced']}")
        print(f"   Prune candidates: {stats['pruned']}")
        print(f"\n✅ Consolidation complete")


if __name__ == "__main__":
    main()
