# Memory Architecture Theory

> Based on: "인간 기억 구조의 벡터DB 모사 가능성에 관한 사고실험"

## Core Thesis

**"벡터는 기억 자체가 아니라 기억을 찾아가는 열쇠(key)다."**

**"더 큰 벡터 공간이 아니라 더 나은 디코더를 만들어야 한다."**

## Dual-Layer Architecture

```
┌─────────────────────────────────────────┐
│          Conscious Layer (I/O)          │
│                                         │
│  INPUT ──▶ [LLM Context] ──▶ OUTPUT    │
│           · Working memory (7±2 chunks) │
│           · Current emotional state     │
└──────────────┬──────────────────────────┘
               │ Only important things flow down
               ▼
┌─────────────────────────────────────────┐
│         Unconscious Layer               │
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ Index Keys   │  │ Multimodal      │ │
│  │ FTS5 keyword │──│ Payloads        │ │
│  │ Vector 384d  │  │ text/audio/img  │ │
│  │ + metadata   │  │                 │ │
│  └──────────────┘  └─────────────────┘ │
│        ↑                                │
│  [Background Processes]                 │
│  · Decay (forgetting)                   │
│  · Clustering (association)             │
│  · Re-indexing (reinterpretation)       │
│  · Emotional drift (rosy retrospection) │
└─────────────────────────────────────────┘
```

## Eidolon Implementation Map

| Theory Concept | Human Brain | Eidolon Component |
|---|---|---|
| Conscious I/O | Prefrontal cortex | LLM context window |
| Episode indexing | Hippocampus | FTS5 + metadata (`memory_meta`) |
| Emotion tagging | Amygdala | `valence` / `arousal` fields |
| Semantic storage | Neocortex | Multimodal payloads (files) |
| Sleep consolidation | SWS replay | `consolidation.py` (cron job) |
| Forgetting curve | Synaptic pruning | `decay_rate` + periodic decay |
| Memory association | Neural connections | `memory_links` table |
| Reinterpretation | Reconsolidation | `reindex.py` |

## Key Insight: Memory Compression Levels

| System | Dimensions | Notes |
|---|---|---|
| Human fresh episode | ~100-300 | Reconstructable |
| Human old memory | ~10-50 | Semantic/emotional summary only |
| "I was happy then" | ~5-10 | Sensory anchor |
| Text embedding (384d) | 384 | Matches human episodic range |
| Eidolon FTS5 | keyword-based | Complements vector with exact match |

**384 dimensions ≈ human long-term memory compression level.**

## Background Processes

### 1. Consolidation (`consolidation.py`)
- **Decay:** Unretrieved memories fade (Ebbinghaus curve)
- **Reinforce:** Frequently recalled memories strengthen
- **Prune:** Memories below threshold are soft-deleted
- Run as cron/heartbeat job

### 2. Re-indexing (`reindex.py`)  
- **Discover:** New memories find semantic neighbors in existing memories
- **Link:** Create bidirectional `memory_links`
- **Enrich:** Old memories gain new tags from new context
- "그때 그 사람이 왜 그랬는지 이제 이해가 돼"

### 3. Emotional Drift (in consolidation)
- Current mood slowly overwrites old `valence` (alpha=0.05)
- Rosy retrospection: accumulated micro-shifts over time
- Payload (facts) unchanged; interpretation (valence) evolves

## Search: Human-Like Recall (`search-v2.py`)

```python
final_score = (
    keyword_score    * 0.30   # What matches
    + emotion_score  * 0.15   # Mood congruence
    + time_weight    * 0.10   # Recency
    + recall_boost   * 0.10   # Familiarity
    + current_strength * 0.10 # Not forgotten
    + (keyword * strength) * 0.25  # Interaction
)
```

This explains why:
- Sad people recall sad memories more easily (emotion_score)
- Traumatic memories persist despite time (high consolidation)
- A smell triggers a 20-year-old memory (sensory anchor match)

## Future: Multimodal Payloads

Current: text-only payloads (markdown files)

Planned:
```python
class MemoryRecord:
    vector: np.array      # 384d - search key
    text: str             # Linguistic narrative
    audio: str | None     # Sound anchor (file path)
    image: str | None     # Visual anchor
    video: str | None     # Episode clip
    source_modality: list # ["visual", "auditory", ...]
```

The bottleneck is not dimension count but a universal sensory encoder
that maps all modalities into one continuous embedding space.

## References

1. Miller, G. A. (1956). The magical number seven, plus or minus two.
2. Ebbinghaus, H. (1885). Über das Gedächtnis.
3. Bartlett, F. C. (1932). Remembering.
4. O'Keefe, J. & Dostrovsky, J. (1971). Place cells.
5. Radford, A. et al. (2021). CLIP.

---

*This architecture design is inspired by a thought experiment on modeling
human memory with vector databases. The original paper explores consciousness/
unconsciousness as dual layers and proposes multimodal memory vectors with
emotional metadata.*
