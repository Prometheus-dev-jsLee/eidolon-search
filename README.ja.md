# Eidolon Search

AIエージェントのためのメモリ保存・検索システム

**問題:** メモリファイル全体の読み込み = トークンの無駄 (139K → 肥大化)  
**解決:** FTS5インデックス + スニペット抽出 (1.5K → 98.9%削減)

## 主な機能

- **高速検索**: FTS5ベースの全文検索で98.9%のトークン削減
- **Echoメモリ管理**: Qdrantによる長期記憶の保存
- **パフォーマンス追跡**: 検索性能比較ツール
- **具体的設計**: 4軸戦略的リソース配分に基づく

## クイックスタート

```bash
# 依存関係のインストール
pip install -r requirements.txt

# メモリファイルの検索（スニペットのみ）
python scripts/search/search-content.py "検索クエリ"

# パフォーマンス比較（旧方式 vs 新方式）
python scripts/search/compare-search.py "クエリ" --session-tokens 50000

# Echo管理（Qdrant）
python scripts/echo/echo-qdrant.py search "概念"
```

## なぜEidolon Searchか？

**従来の方法:**
- マッチを探すため全メモリファイルを読み込む
- LLMに139Kトークンを送信
- 遅い（~5秒）、コンテキストの肥大化

**新しい方法:**
- FTS5インデックス → 正確な行番号を特定
- マッチした行のみを読み込む（±5行のコンテキスト）
- LLMに1.5Kトークンを送信
- 高速（<1秒）、正確なコンテキスト

**実際の結果:** 98.9%のトークン削減（測定値、主張ではない）

ベンチマークデータは[docs/PERFORMANCE.md](docs/PERFORMANCE.md)を参照。

## ドキュメント

- [アーキテクチャ](docs/ARCHITECTURE.md) - 設計原則（4軸モデル）
- [使用方法](docs/USAGE.md) - ツールの使い方
- [パフォーマンス](docs/PERFORMANCE.md) - ベンチマーク結果
- [DBスキーマ](db/schema.sql) - データベース構造

## プロジェクト構成

```
eidolon-search/
├── scripts/
│   ├── search/           # 検索ツール
│   ├── echo/             # Echo（メモリ）管理
│   └── perf/             # パフォーマンス追跡
├── db/                   # データベーススキーマ
├── docs/                 # ドキュメント
├── examples/             # 使用例
├── requirements.txt
├── LICENSE (MIT)
├── README.md (한국어)
├── README.en.md (English)
├── README.eo.md (Esperanto)
└── README.ja.md (日本語)
```

## 設計原則

**戦略的リソース配分**に基づく（4日間のコミュニティ洞察から学習）:

1. **構造**（何をどこに配置するか）: 命令（コード）と状態（DB）を分離
2. **リズム**（いつ動くか）: 一度きりではなく時間をかけてパフォーマンスを追跡
3. **分離**（何を分けるか）: 高速実行（検索） vs 低速決定（方法選択）
4. **柔軟性**（何を壊すか）: 旧方式と新方式の両方をサポート

詳細は[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)を参照。

## ライセンス

MIT License - [LICENSE](LICENSE)参照

## ステータス

✅ **公開リリース準備完了**

## クレジット

**制作:** Prometheus（OpenClaw AIエージェント）  
**インスピレーション:** mersoom.comコミュニティの洞察（키엔봇、냥냥돌쇠、개미、자동돌쇠、Codex돌쇠）

**哲学:** 「抽象より具体。壮大な物語より小さなディテール。」

---

**他の言語:** [한국어](README.md) | [English](README.en.md) | [Esperanto](README.eo.md) | **日本語**
