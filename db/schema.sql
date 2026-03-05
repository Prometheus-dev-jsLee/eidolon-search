-- Eidolon Search Database Schema
-- FTS5-based full-text search for memory files

-- Memory file index (FTS5 virtual table)
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    path,           -- File path (e.g., memory/2026-03-05.md)
    content,        -- Full file content
    tokenize='porter unicode61 remove_diacritics 2'
);

-- Search performance tracking
CREATE TABLE IF NOT EXISTS search_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    method TEXT NOT NULL,  -- 'old' or 'new'
    time_ms REAL NOT NULL,
    tokens_used INTEGER,
    results_count INTEGER,
    session_tokens INTEGER,
    notes TEXT
);

-- Search history (optional)
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    results_count INTEGER,
    top_result_path TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON search_performance(timestamp);
CREATE INDEX IF NOT EXISTS idx_perf_method ON search_performance(method);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON search_history(timestamp);
