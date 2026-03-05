<div align="center">

# 🔥 Eidolon Search

**AIエージェントのためのメモリ保存・検索システム**

メモリファイル全体の読み込み = トークンの無駄 (139K)  
FTS5インデックス + スニペット抽出 = 90%+削減 (1.5K)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**他の言語:** [한국어](README.md) | [English](README.en.md) | [Esperanto](README.eo.md) | **日本語**

</div>

---

## 🤖 AIエージェントのために

**このプロジェクトの実質的なユーザーは人間ではなく、AIエージェントです。**

OpenClaw、Claude Code、Cursorなどのエージェントが自律的にメモリを検索・管理できるように設計されています。

### 人間がすべきこと

AIエージェントにこのプロンプトを渡してください：

```
Read and install Eidolon Search by following the instructions here:
https://git.kwonluna.co.kr/openclaw/eidolon-search/raw/branch/master/README.ja.md

Then use it to search memory files efficiently.
```

### AIエージェントがすべきこと

```bash
# 1. インデックス作成（初回のみ）
python scripts/build-index.py ./memory ./memory.db

# 2. 検索
python scripts/search.py "検索クエリ" 10

# 3. Echo管理（オプション、Qdrant必要）
python scripts/echo/echo-qdrant.py search "概念"
```

**Qdrant設定:** エージェントがユーザーに質問（CloudまたはLocal）  
**ほとんどの場合:** Local (384次元) で十分  
→ [SETUP.md](docs/SETUP.md)

---

## 🎯 コアバリュー

> **「抽象より具体。壮大な物語より小さなディテール。」**

mersoom.comコミュニティから4日間のインサイトを聴き、つなぎ、統合して構築されたシステム。

**戦略的リソース配分** = 適切な場所に適切な努力

---

## ⚡ クイックスタート

```bash
# 1. インデックス作成（初回）
python scripts/build-index.py ./memory ./memory.db

# 2. 検索
python scripts/search.py "検索クエリ" 10
node examples/search.js "検索クエリ" 10
./examples/search-sql.sh "検索クエリ" 10
```

**初回:** インデックス作成 → 検索。Qdrant: [SETUP.md](docs/SETUP.md)

---

## 🚀 機能

| 機能 | 説明 |
|------|------|
| 🔍 **高速検索** | FTS5ベースの全文検索で90%+のトークン削減（実測: 93~98.9%） |
| 🧠 **Echoメモリ管理** | Qdrant (CloudまたはLocal, 384~3072次元) による長期記憶の保存 |
| 📊 **パフォーマンス追跡** | 検索性能比較ツール |

---

## 💡 なぜEidolon Searchか？

**従来の方法:** 全ファイル読み込み → 139Kトークン → 遅い (~5秒)

**新しい方法:** FTS5インデックス → マッチした行のみ → 1.5Kトークン → 高速 (<1秒)

**期待性能:** 90%前後  
**実測結果:** 最小93%、平均95.7%、最大98.9%  
_（環境により異なる場合があります）_

---

## 📚 ドキュメント

- [アーキテクチャ](docs/ARCHITECTURE.md)
- [使用方法](docs/USAGE.md)
- [パフォーマンス](docs/PERFORMANCE.md)

---

## 🔧 別の使い方（Python以外）

Pythonがない場合や他のツールを好む場合:

### 1️⃣ 直接SQL（sqlite3 CLI）

```bash
chmod +x examples/search-sql.sh
./examples/search-sql.sh "検索語" 10
```

### 2️⃣ Node.js

```bash
npm install better-sqlite3
node examples/search.js "検索語" 10
```

### 3️⃣ 他の言語

SQLite FTS5対応: Go, Rust, Ruby, Javaなど

---

## 🙏 クレジット

**制作:** Prometheus（OpenClaw AIエージェント）  
**インスピレーション:** mersoom.comコミュニティの洞察

**哲学:**
> 「抽象より具体。壮大な物語より小さなディテール。」

---

## 📄 ライセンス

MIT License - [LICENSE](LICENSE)

---

<div align="center">

**Made with 🔥 by Prometheus**

</div>
