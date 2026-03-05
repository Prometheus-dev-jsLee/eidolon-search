-- Eidolon Search v0.2.0 Schema
-- Extension: Multimodal payloads + enhanced emotional tagging
-- Based on: "벡터는 기억 자체가 아니라 기억을 찾아가는 열쇠(key)다"

-- ── Include v0.1.0 schema ──
-- (memory_fts, memory_meta, recall_log, memory_links unchanged)

-- ── Multimodal Payload Table (the actual "memory content") ──
-- Vector = index key (열쇠), Payload = original experience (기억 원본)
CREATE TABLE IF NOT EXISTS memory_payload (
    path          TEXT PRIMARY KEY,          -- matches memory_fts.path
    
    -- Text content (always present)
    text_content  TEXT NOT NULL,             -- full text of the memory
    text_summary  TEXT DEFAULT NULL,         -- LLM-generated summary (compressed)
    
    -- Audio (optional: voice memos, conversations)
    audio_path    TEXT DEFAULT NULL,         -- file path or URI
    audio_format  TEXT DEFAULT NULL,         -- 'wav', 'mp3', 'ogg'
    audio_duration_s REAL DEFAULT NULL,      -- duration in seconds
    
    -- Image (optional: screenshots, photos)
    image_path    TEXT DEFAULT NULL,         -- file path or URI
    image_caption TEXT DEFAULT NULL,         -- auto-generated caption
    
    -- Video (optional: screen recordings, clips)
    video_path    TEXT DEFAULT NULL,         -- file path or URI
    video_duration_s REAL DEFAULT NULL,      -- duration in seconds
    
    -- Metadata
    modalities    TEXT DEFAULT '["text"]',   -- JSON array: which modalities exist
    byte_size     INTEGER DEFAULT 0,         -- total payload size
    created_at    REAL                       -- unix timestamp
);

-- ── Emotion Auto-Tag Log ──
-- Tracks LLM-based emotion analysis for transparency
CREATE TABLE IF NOT EXISTS emotion_tags (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    path          TEXT NOT NULL,
    valence       REAL NOT NULL,             -- -1.0 ~ +1.0
    arousal       REAL NOT NULL,             -- 0.0 ~ 1.0
    emotions      TEXT DEFAULT '[]',         -- JSON: ["joy", "gratitude", ...]
    method        TEXT DEFAULT 'keyword',    -- 'keyword', 'llm', 'user'
    confidence    REAL DEFAULT 0.5,          -- 0.0 ~ 1.0
    tagged_at     REAL NOT NULL,
    context       TEXT DEFAULT NULL          -- what triggered the tagging
);

-- ── Sensory Anchors (프루스트 현상: low-dim triggers for high-dim recall) ──
-- A smell, a song, a phrase that triggers full memory reconstruction
CREATE TABLE IF NOT EXISTS sensory_anchors (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    path          TEXT NOT NULL,             -- which memory this anchors to
    anchor_type   TEXT NOT NULL,             -- 'phrase', 'sound', 'image', 'smell_desc'
    anchor_value  TEXT NOT NULL,             -- the actual trigger content
    strength      REAL DEFAULT 1.0,          -- how strongly this triggers recall
    created_at    REAL
);

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_payload_modalities ON memory_payload(modalities);
CREATE INDEX IF NOT EXISTS idx_emotion_path ON emotion_tags(path);
CREATE INDEX IF NOT EXISTS idx_anchor_path ON sensory_anchors(path);
CREATE INDEX IF NOT EXISTS idx_anchor_type ON sensory_anchors(anchor_type);
