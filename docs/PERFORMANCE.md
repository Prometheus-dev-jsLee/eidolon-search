# Performance

Real-world benchmark results (not theoretical claims).

## Benchmark: "Physical AI" search

**Date:** 2026-03-03

**Setup:**
- Session tokens: 139,000
- Memory files: 27 files
- Query: "Physical AI"

**Results:**

| Method | Tokens Used | Time | Results |
|--------|-------------|------|---------|
| Old (read full files) | 139,000 | ~5s | 3 files |
| New (snippet only) | 1,500 | <1s | 3 snippets |

**Token reduction:** 98.9% (139K → 1.5K)

**Why it matters:**

Before: Reading entire files to find matches = context bloat
After: Read only matched snippets = precise context

## How it works

**Old method:**
1. Search query → Find matching files
2. Read ALL files (memory_search tool)
3. Send 139K tokens to LLM

**New method:**
1. FTS5 index → Find exact line numbers
2. Read ONLY matched lines (±5 context)
3. Send 1.5K tokens to LLM

## Trade-offs

**Pros:**
- 98.9% token reduction
- <1s search time
- Same accuracy

**Cons:**
- Requires FTS5 index build
- Less context (but that's the point)

## Measured, not claimed

All numbers from actual usage:
- See `perf/search-performance.jsonl` for raw data
- Run `python3 scripts/perf/search-perf-report.py --markdown` for latest report
