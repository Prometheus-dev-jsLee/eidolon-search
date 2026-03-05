# Usage Guide

## Installation

```bash
# Clone or download the project
cd eidolon-search

# Install dependencies
pip install -r requirements.txt
```

## Search Memory Files

**Basic search:**

```bash
python3 scripts/search/search-content.py "your query"
```

**Example:**

```bash
python3 scripts/search/search-content.py "Physical AI"
```

**Output:**

```
Found 3 results:
1. memory/2026-03-02.md#L45-50
2. memory/2026-02-28.md#L120-125
...
```

## Compare Search Performance

Track old vs new search methods:

```bash
python3 scripts/search/compare-search.py "query" --session-tokens 50000
```

**What it does:**

1. Search with old method (read full files)
2. Search with new method (snippet only)
3. Log performance to `perf/search-performance.jsonl`

## Echo Management (Qdrant)

**Search long-term memory:**

```bash
python3 scripts/echo/echo-qdrant.py search "concept"
```

**Upload daily echo:**

```bash
python3 scripts/echo/echo-qdrant.py upload memory/echo-2026-03-05.md
```

**Status check:**

```bash
python3 scripts/echo/echo-qdrant.py status
```

## Generate Performance Report

```bash
python3 scripts/perf/search-perf-report.py --markdown > report.md
```

**Output:**

- Comparison table (old vs new)
- Token reduction %
- Time savings

## Tips

**When to use which:**

- **search-content.py**: Quick search in memory files
- **compare-search.py**: Performance testing (track improvement)
- **echo-qdrant.py**: Long-term memory (insights, not raw logs)

**Best practices:**

1. Run `compare-search.py` periodically to track performance
2. Use Echo for curated insights, not daily logs
3. Keep search queries specific (better results)
