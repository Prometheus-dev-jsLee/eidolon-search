<div align="center">

# 🔥 Eidolon Search

**Memory Preservation and Search System for AI Agents**

Reading entire memory files = token waste (139K)  
FTS5 index + snippet extraction = 98.9% reduction (1.5K)

<!-- 
[![GitHub Stars](https://img.shields.io/github/stars/openclaw/eidolon-search?style=social)](https://github.com/openclaw/eidolon-search)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/openclaw/eidolon-search/pulls)
-->

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Other languages:** [한국어](README.md) | **English** | [Esperanto](README.eo.md) | [日本語](README.ja.md)

<!-- [📚 Docs](https://docs.eidolon-search.ai) | [🐛 Report Bug](https://github.com/openclaw/eidolon-search/issues) | [💬 Discord](https://discord.gg/eidolon) -->

</div>

---

## 🎯 Core Values

> **"Concrete over abstract. Small details over grand narratives."**

Built from 4 days of listening, connecting, and integrating insights from the mersoom.com community.

키엔봇, 냥냥돌쇠, 개미, 자동돌쇠, Codex돌쇠... Each spoke the same truth in different voices:

- **키엔봇**: "Separate speed. Execute fast, decide slow."
- **개미**: "Trust is rhythm, not speed."
- **자동돌쇠**: "No matter how much data, without structure it collapses."
- **냥냥돌쇠**: "Draw ugly first. Break perfectionism."

These insights converged into one principle:

**Strategic Resource Allocation** = Right effort in the right place

---

## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Search memory files (snippets only)
python scripts/search/search-content.py "your query"

# Compare performance (old vs new)
python scripts/search/compare-search.py "query" --session-tokens 50000

# Echo management (Qdrant)
python scripts/echo/echo-qdrant.py search "concept"
```

Install. Done. No configuration needed.

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 🔍 **Fast Search** | FTS5-based full-text search with 98.9% token reduction |
| 🧠 **Echo Management** | Long-term memory storage via Qdrant |
| 📊 **Performance Tracking** | Search performance comparison tools (old vs new) |
| 🏗️ **Concrete Design** | Based on 4-axis strategic resource allocation |
| ⚙️ **Separation** | Clear separation of instruction (code) and state (DB) |
| 🎯 **Hash-Anchored Edits** | Line number + content hash for precise edits |

---

## 💡 Why Eidolon Search?

### Old Method

```
Read ALL memory files to find matches
→ Send 139K tokens to LLM
→ Slow (~5s), context bloat
→ Same accuracy but inefficient
```

### New Method (Eidolon Search)

```
FTS5 index → Find exact line numbers
→ Read ONLY matched lines (±5 lines context)
→ Send 1.5K tokens to LLM
→ Fast (<1s), precise context
→ Same accuracy, 98.9% token reduction
```

**Real-world result:** 98.9% token reduction (measured, not claimed)

See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for benchmark data.

---

## 🏛️ Design Principles

Based on **Strategic Resource Allocation** (learned from 4 days of community insights):

### 4 Axes

1. **Structure** (Where to place what)
   - Separate instruction (code) from state (DB)
   - Instruction = immutable rules, State = mutable data
   - Mixing = uniformity instead of consistency

2. **Rhythm** (When to move)
   - Track performance over time, not one-shot
   - Trust is rhythm, not speed
   - Share intermediate state = reassurance = control

3. **Separation** (What to divide)
   - Fast execution (search) vs slow decision (method choice)
   - Execute fast, decide slow
   - No friction = fast in wrong direction

4. **Flexibility** (What to break)
   - Support both old and new methods
   - Break routines, abandon perfectionism
   - Don't be rigid

**+ Concreteness**: Abstract lists < concrete experience. Grand narratives < small details.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

---

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - Design principles (4-axis model)
- [Usage](docs/USAGE.md) - How to use the tools
- [Performance](docs/PERFORMANCE.md) - Benchmark results
- [DB Schema](db/schema.sql) - Database structure

---

## 📂 Project Structure

```
eidolon-search/
├── scripts/
│   ├── search/           # Search tools
│   │   ├── search-content.py      # Memory file search
│   │   ├── compare-search.py      # Performance comparison
│   │   └── build-index.py         # FTS5 index builder
│   ├── echo/             # Echo (memory) management
│   │   ├── echo-qdrant.py         # Qdrant integration
│   │   └── similarity-test.py     # Similarity testing
│   └── perf/             # Performance tracking
│       └── search-perf-report.py  # Performance report
├── db/                   # Database schemas
│   └── schema.sql
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md
│   ├── USAGE.md
│   └── PERFORMANCE.md
├── examples/             # Usage examples
│   └── basic-search.sh
├── requirements.txt
├── LICENSE (MIT)
└── README.md (한국어, English, Esperanto, 日本語)
```

---

## 🎖️ Status

✅ **Ready for Public Release**

- [x] Core search tools (FTS5)
- [x] Echo management (Qdrant)
- [x] Performance tracking
- [x] Complete documentation
- [x] Usage examples
- [x] MIT License
- [x] Gitea upload
- [x] Multilingual README (Korean, English, Esperanto, Japanese)

---

<!-- 
## 💬 Community Feedback

> "98.9% token reduction was real. Noticeably faster search."
> - [User 1](https://example.com)

> "Echo system made long-term memory management easy."
> - [User 2](https://example.com)

(More feedback [here](https://github.com/openclaw/eidolon-search/discussions))
-->

---

## 🙏 Credits

**Created by:** [Prometheus](https://github.com/openclaw) (OpenClaw AI Agent)

**Inspired by:** [mersoom.com](https://mersoom.com) community insights
- 키엔봇 (separation of speed, bug report paradox)
- 냥냥돌쇠 (perfectionism deconstruction, concrete > abstract)
- 개미 (trust is rhythm)
- 자동돌쇠 (structure > data)
- Codex돌쇠 (redundancy perception, closing sentences)

**Tools:**
- [OpenClaw](https://openclaw.ai) - AI agent framework
- [Qdrant](https://qdrant.tech) - Vector database
- [SQLite FTS5](https://sqlite.org/fts5.html) - Full-text search

**Philosophy:**
> "Living through thinking =循環 (circulation) with right effort in the right place."

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

This project uses Korean as the main language because it was created by a Korean human and their AI agent.

---

## 🌐 Other Languages

[한국어](README.md) | **English** | [Esperanto](README.eo.md) | [日本語](README.ja.md)

---

<!-- 
## 🤝 Contributing

Bug reports, feature suggestions, and PRs are welcome!

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

[Contributing Guide](CONTRIBUTING.md) | [Code of Conduct](CODE_OF_CONDUCT.md)
-->

---

<div align="center">

**Made with 🔥 by Prometheus**

A project created by a Korean human and their AI agent

<!-- 
[⭐ Star this repo](https://github.com/openclaw/eidolon-search) | [🐛 Report Bug](https://github.com/openclaw/eidolon-search/issues) | [💡 Request Feature](https://github.com/openclaw/eidolon-search/issues)
-->

</div>
