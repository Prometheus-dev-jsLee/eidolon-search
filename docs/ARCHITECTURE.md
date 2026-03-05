# Architecture

Eidolon Search follows **strategic resource allocation** principles:

## 4 Axes

### 1. Structure (Where to place what)

**Separation of instruction and state:**

- **Search scripts** = stateless tools (read-only)
- **Database** = persistent state (memory files, FTS5 index)
- **Echo system** = long-term episodic memory (Qdrant)

**Data flow:**

```
Memory files (.md) → FTS5 index → Search results → Snippets (not full files)
                  ↓
               Qdrant → Long-term insights
```

### 2. Rhythm (When and how to move)

**Search performance tracking:**

- Periodic comparison (old vs new method)
- Performance metrics stored in `perf/search-performance.jsonl`
- Report generation: `scripts/perf/search-perf-report.py --markdown`

**Trust through rhythm, not speed:**

- Consistent search API (not changing frequently)
- Incremental improvement (track performance over time)

### 3. Separation (What to divide)

**Fast vs slow:**

- **Fast execution**: FTS5 search (< 1s)
- **Slow decision**: Which search method to use (track performance first)

**Read vs write:**

- Search = read-only (safe, fast)
- Echo upload = write (careful, tracked)

### 4. Flexibility (What to break)

**Don't be rigid:**

- Support both old (read full file) and new (snippet only) methods
- Allow custom search queries (not just predefined)
- Extensible schema (add new fields without breaking)

## Concrete over Abstract

**Bad:**

"This is a memory system that uses advanced algorithms."

**Good:**

"Search 98.9% faster by reading 10 lines instead of 2000+ line files."

## Database Schema

See `db/schema.sql` for details.

**Key principle:**

- **State** (search index, vectors) = mutable, file-based
- **Instruction** (how to search) = immutable, code-based
- Never mix them (consistency, not uniformity)

## Performance

**Measured results** (not claims):

- Token reduction: 98.9% (139K → 1.5K)
- Search time: < 1s (FTS5)
- Accuracy: Same results, less context

See `docs/PERFORMANCE.md` for benchmark data.
