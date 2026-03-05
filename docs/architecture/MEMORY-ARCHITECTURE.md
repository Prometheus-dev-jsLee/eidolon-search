# Memory Architecture: Dual-Layer Human Memory Model

> Based on: "인간 기억 구조의 벡터DB 모사 가능성에 관한 사고실험"
> Core thesis: **Vectors are keys to memory, not memory itself.**

## Overview

Eidolon's next evolution models human memory's dual-layer structure:
- **Conscious Layer** = LLM Context Window (working memory, 7±2 chunks)
- **Unconscious Layer** = Vector Index + Multimodal Payload + Background Processes

```
┌─────────────────────────────────────────────┐
│              Conscious Layer                 │
│                                              │
│   INPUT ──▶ [LLM Context Window] ──▶ OUTPUT │
│              · Session context               │
│              · Working memory (7±2 chunks)   │
│              · Current emotional state       │
└──────────────────┬──────────────────────────┘
                   │  Only important things pass
                   ▼
┌─────────────────────────────────────────────┐
│             Unconscious Layer                │
│                                              │
│  ┌──────────────┐   ┌────────────────────┐  │
│  │ Vector Index  │   │ Multimodal Payload │  │
│  │ (384-dim)    │──▶│ text / audio /     │  │
│  │ + metadata   │   │ image / context    │  │
│  └──────────────┘   └────────────────────┘  │
│         ↑                                    │
│  [Background Processes]                      │
│  · Decay (forgetting curve)                  │
│  · Clustering (similar memories)             │
│  · Re-indexing (reinterpretation)            │
│  · Emotional weight adjustment               │
└─────────────────────────────────────────────┘
```

## Key Insight

> 384 dimensions ≈ human long-term memory compression level.
> The bottleneck is NOT dimension count — it's the decoder quality.

Current Eidolon (v0.0.2): FTS5 keyword search = fast, efficient, but flat.
Next Eidolon: FTS5 + Vector search + Emotional metadata + Background processes.

## Memory Record Schema

```python
class MemoryRecord:
    # ── Index Layer (search key) ──
    vector: list[float]       # 384-dim semantic embedding
    fts_content: str          # FTS5 indexed text (keyword search)

    # ── Payload (reconstruction material) ──
    text: str                 # Verbalized narrative / internal monologue
    audio_ref: str | None     # Audio anchor (file path or URL)
    image_ref: str | None     # Visual anchor
    context: dict             # Session context, conversation flow

    # ── Metadata (dynamic properties) ──
    timestamp: float          # When the experience occurred
    valence: float            # Emotional valence: -1.0 (negative) ~ +1.0 (positive)
    arousal: float            # Arousal: 0.0 (calm) ~ 1.0 (intense)
    decay_rate: float         # Forgetting speed (Ebbinghaus parameter)
    consolidation: int        # Recall count (reinforcement)
    source_modality: list     # Encoding source: ["text", "voice", "visual"]
    social_context: list      # Who was involved
    tags: list[str]           # Semantic tags for clustering
```

## Search Function: Human-Like Recall

Standard vector DB: cosine similarity only.
Human memory model: integrates emotion, time, reinforcement.

```python
def memory_search(query_vector, query_text, current_state):
    # 1. Semantic similarity (vector)
    semantic_score = cosine_similarity(query_vector, memory.vector)

    # 2. Keyword match (FTS5) — Eidolon's current strength
    keyword_score = fts5_rank(query_text, memory.fts_content)

    # 3. Emotional affinity — memories matching current mood surface easier
    emotion_score = 1 - abs(current_state.valence - memory.valence)

    # 4. Recency weight — recent memories first, but reinforced ones persist
    time_weight = recency_weight(memory.timestamp)

    # 5. Reinforcement boost — frequently recalled = easier to recall
    recall_boost = log(1 + memory.consolidation) * 0.1

    # 6. Current decay state (forgetting)
    current_strength = memory.decay_rate ** days_elapsed(memory.timestamp)

    return (
        semantic_score   * 0.30
        + keyword_score  * 0.25  # FTS5 — Eidolon's differentiator
        + emotion_score  * 0.15
        + time_weight    * 0.10
        + recall_boost   * 0.10
        + current_strength * 0.10
    )
```

### Why Hybrid (Vector + FTS5)?

- **Vector search**: "memories that feel similar" (semantic proximity)
- **FTS5 search**: "memories that contain this exact thing" (keyword precision)
- Human memory uses both: vague association + precise recall
- FTS5 is Eidolon's unique advantage — 90%+ token reduction stays

## Background Processes (Unconscious)

```python
def consolidation_job():
    """Nightly batch process — equivalent to sleep consolidation"""

    # 1. Decay: unretrieved memories fade
    for memory in all_memories():
        days = days_since_recall(memory)
        if days > 7:
            memory.decay_rate *= 0.97  # Ebbinghaus approximation

    # 2. Clustering: reinforce connections between similar memories
    clusters = semantic_cluster(all_vectors(), eps=0.15)
    for cluster in clusters:
        reinforce_connections(cluster)

    # 3. Re-indexing: today's experience changes meaning of old memories
    #    "Now I understand why they said that"
    today = get_today_memories()
    for memory in find_affected_by(today):
        memory.vector = re_encode(
            original=memory.payload,
            new_context=today
        )

    # 4. Emotional re-evaluation
    #    Current state slowly overwrites past valence → rosy retrospection
    for memory in recently_recalled():
        memory.valence = blend(
            memory.valence,
            current_mood.valence,
            alpha=0.05  # Very slow → gradual memory beautification
        )
```

## Implementation Phases

### Phase 1: Schema Extension (v0.1.0)
- [ ] Add `valence`, `arousal`, `decay_rate`, `consolidation` to SQLite schema
- [ ] Add `vector` BLOB column (384-dim, optional)
- [ ] Hybrid search: FTS5 score + metadata weighting
- [ ] Keep backward compatibility with v0.0.x

### Phase 2: Vector Integration (v0.2.0)
- [ ] Embed memories using `all-MiniLM-L6-v2` (384-dim)
- [ ] Qdrant integration for vector search
- [ ] Hybrid scoring: FTS5 + cosine similarity + metadata
- [ ] Emotion extraction from text (simple sentiment analysis)

### Phase 3: Background Processes (v0.3.0)
- [ ] Decay job (cron/heartbeat based)
- [ ] Consolidation counting (auto-increment on recall)
- [ ] Semantic clustering
- [ ] Re-indexing pipeline

### Phase 4: AIRI Integration (v0.4.0)
- [ ] AIRI memory module interface
- [ ] Multimodal payload support (audio/image refs)
- [ ] Real-time emotional state from AIRI's interaction layer
- [ ] Memory reconstruction via LLM context injection

## Theoretical Foundation

| Human Memory | System Equivalent |
|-------------|-------------------|
| Hippocampus (encoding/indexing) | Embedding model + Vector index |
| Amygdala (emotional tagging) | valence/arousal metadata |
| Neocortex (semantic storage) | Multimodal payload store |
| SWS consolidation | Nightly batch re-indexing |
| Forgetting curve | decay_rate field + periodic decay |
| Working memory | LLM context window |
| Proust phenomenon (smell → memory) | Low-dim anchor → high-dim reconstruction |

## Key Principle

> **"We need a better decoder, not a bigger vector space."**
>
> The richness of memory comes not from storage dimensions,
> but from the quality of reconstruction.
> A 5-dimensional emotional anchor can trigger
> a full experiential reconstruction — just like a smell
> bringing back a 20-year-old memory.

---

*This architecture transforms Eidolon from a search tool into a cognitive memory system.*
