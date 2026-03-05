-- Eidolon Search v0.1.0 Schema
-- Dual-layer memory architecture: FTS5 (keyword) + metadata (human-like recall)
-- Based on: "인간 기억 구조의 벡터DB 모사 가능성에 관한 사고실험"

-- ── FTS5 Virtual Table (keyword search, unchanged from v0.0.x) ──
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
    path,
    content,
    tokenize='porter unicode61 remove_diacritics 2'
);

-- ── Memory Metadata Table (human-like memory properties) ──
CREATE TABLE IF NOT EXISTS memory_meta (
    path          TEXT PRIMARY KEY,          -- matches memory_fts.path
    
    -- Temporal
    created_at    REAL,                      -- unix timestamp: when memory was formed
    last_recalled REAL,                      -- unix timestamp: last time this memory was retrieved
    
    -- Emotional dimensions
    valence       REAL DEFAULT 0.0,          -- -1.0 (negative) ~ +1.0 (positive)
    arousal       REAL DEFAULT 0.5,          -- 0.0 (calm) ~ 1.0 (intense)
    
    -- Memory dynamics
    decay_rate    REAL DEFAULT 0.95,         -- Ebbinghaus forgetting curve parameter
    consolidation INTEGER DEFAULT 0,         -- recall count (reinforcement)
    strength      REAL DEFAULT 1.0,          -- current memory strength (computed)
    
    -- Context
    source        TEXT DEFAULT 'text',       -- encoding source: text, voice, image, mixed
    tags          TEXT DEFAULT '[]',         -- JSON array of semantic tags
    social        TEXT DEFAULT '[]',         -- JSON array of people involved
    
    -- Vector (Phase 2, optional)
    vector        BLOB DEFAULT NULL          -- 384-dim float32 embedding (1536 bytes)
);

-- ── Recall Log (tracks every memory retrieval) ──
CREATE TABLE IF NOT EXISTS recall_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    path          TEXT NOT NULL,             -- which memory was recalled
    query         TEXT NOT NULL,             -- what query triggered recall
    score         REAL,                      -- retrieval score
    recalled_at   REAL NOT NULL,             -- unix timestamp
    context       TEXT DEFAULT NULL          -- optional: session context
);

-- ── Memory Links (associations between memories) ──
CREATE TABLE IF NOT EXISTS memory_links (
    source_path   TEXT NOT NULL,
    target_path   TEXT NOT NULL,
    link_type     TEXT DEFAULT 'semantic',   -- semantic, temporal, emotional, causal
    strength      REAL DEFAULT 1.0,
    created_at    REAL,
    PRIMARY KEY (source_path, target_path, link_type)
);

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_meta_valence ON memory_meta(valence);
CREATE INDEX IF NOT EXISTS idx_meta_strength ON memory_meta(strength);
CREATE INDEX IF NOT EXISTS idx_meta_last_recalled ON memory_meta(last_recalled);
CREATE INDEX IF NOT EXISTS idx_recall_log_path ON recall_log(path);
CREATE INDEX IF NOT EXISTS idx_recall_log_time ON recall_log(recalled_at);
