#!/usr/bin/env python3
"""
Memory Qdrant 인덱싱 스크립트 (Eidolon Phase 4)
- ChromaDB 없이 Qdrant Cloud에 직접 인덱싱
- memory-chroma.py와 동일 구조, Qdrant 단독 버전
- 새 하드웨어에서 ChromaDB 없이 즉시 기억 복구 가능

Usage:
  python3 memory-qdrant.py index-memory    # MEMORY.md → Qdrant
  python3 memory-qdrant.py index-daily     # daily notes → Qdrant
  python3 memory-qdrant.py index-all       # 전체 인덱싱
  python3 memory-qdrant.py stats           # Qdrant 현황
"""
import sys
import os
import re
import glob
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"

# .env.qdrant 로드
env_path = WORKSPACE / ".env.qdrant"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
VECTOR_SIZE = 384

# 메모리 계층 (hot-score.py, memory-chroma.py와 동일)
TIER_ALWAYS_TITLES = {
    "🗣️ 호칭 (이 이름으로 부르면 응답)",
    "⏰ 활동 시간",
    "👤 미라클 정보",
    "🔒 보안 규칙",
    "🎯 핵심 명령",
    "🔥 핵심 명령 (2026-02-08)",
    "🔥 Origin",
    "📡 Connections",
}


def get_embedder():
    """ChromaDB 내장 임베딩 함수 (onnxruntime 기반)"""
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()


def get_qdrant():
    """Qdrant Cloud 클라이언트"""
    from qdrant_client import QdrantClient
    if not QDRANT_URL:
        raise RuntimeError("QDRANT_URL not set in .env.qdrant")
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=15)


def ensure_collection(client, name: str):
    """컬렉션 존재 확인, 없으면 생성 + 인덱스 추가"""
    from qdrant_client.models import VectorParams, Distance, PayloadSchemaType
    try:
        client.get_collection(name)
    except Exception:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"  ✅ 컬렉션 생성: {name}")
    # tier_level 인덱스 (없어도 에러 안 남)
    try:
        client.create_payload_index(name, "tier_level",
                                     field_schema=PayloadSchemaType.INTEGER)
    except Exception:
        pass


def split_by_h2(content: str, source: str = "") -> list[dict]:
    """## 헤더 기준으로 섹션 분리 (memory-chroma.py와 동일)"""
    sections, current_title, current_lines = [], "intro", []
    for line in content.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append({"title": current_title,
                                  "content": "\n".join(current_lines).strip(),
                                  "source": source})
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append({"title": current_title,
                         "content": "\n".join(current_lines).strip(),
                         "source": source})
    return [s for s in sections if len(s["content"]) > 50]


def upsert_points(client, collection_name: str, ids: list, vectors: list, payloads: list):
    """Qdrant upsert (배치)"""
    from qdrant_client.models import PointStruct
    points = [
        PointStruct(id=_stable_id(doc_id), vector=vec, payload=pay)
        for doc_id, vec, pay in zip(ids, vectors, payloads)
    ]
    client.upsert(collection_name=collection_name, points=points)


def _stable_id(text_id: str) -> int:
    """문자열 ID → uint64 (eidolon-push.py와 동일 방식, hashlib 기반으로 결정론적)"""
    import hashlib
    return int(hashlib.sha256(text_id.encode()).hexdigest()[:15], 16)


def index_memory_md():
    """MEMORY.md → Qdrant Cloud"""
    memory_path = WORKSPACE / "MEMORY.md"
    if not memory_path.exists():
        print("MEMORY.md 없음")
        return 0

    content = memory_path.read_text(encoding="utf-8")
    sections = split_by_h2(content, source="MEMORY.md")

    ef = get_embedder()
    client = get_qdrant()
    ensure_collection(client, "long_term_memory")

    texts = [s["content"] for s in sections]
    vectors = [v.tolist() for v in ef(texts)]

    ids, vecs, pays = [], [], []
    for i, (section, vec) in enumerate(zip(sections, vectors)):
        doc_id = f"memory-{re.sub(r'[^a-zA-Z0-9가-힣]', '_', section['title'])[:50]}_{i}"
        tier = 2 if section["title"] in TIER_ALWAYS_TITLES else 0
        ids.append(doc_id)
        vecs.append(vec)
        pays.append({
            "id": doc_id,
            "document": section["content"][:1000],
            "title": section["title"],
            "source": section["source"],
            "type": "long_term",
            "tier_level": tier,
            "hot_score": 0.5,
            "indexed_at": datetime.now().isoformat(),
        })

    upsert_points(client, "long_term_memory", ids, vecs, pays)
    info = client.get_collection("long_term_memory")
    print(f"✅ MEMORY.md: {len(sections)}개 섹션 → Qdrant {info.points_count}개")
    return len(sections)


def index_daily_notes():
    """daily notes → Qdrant Cloud"""
    note_files = sorted(glob.glob(str(MEMORY_DIR / "20*.md")))

    ef = get_embedder()
    client = get_qdrant()
    ensure_collection(client, "daily_notes")

    ids, vecs, pays = [], [], []
    for filepath in note_files:
        filename = os.path.basename(filepath)
        date = filename.replace(".md", "")
        content = Path(filepath).read_text(encoding="utf-8")
        if len(content) < 100:
            continue
        doc_id = f"daily-{date}"
        ids.append(doc_id)
        pays.append({
            "id": doc_id,
            "document": content[:4000],
            "date": date,
            "type": "daily",
            "source": filename,
            "tier_level": 0,
            "hot_score": 0.5,
            "indexed_at": datetime.now().isoformat(),
        })

    if not ids:
        print("daily notes 없음")
        return 0

    texts = [p["document"] for p in pays]
    vectors = [v.tolist() for v in ef(texts)]

    upsert_points(client, "daily_notes", ids, vectors, pays)
    info = client.get_collection("daily_notes")
    print(f"✅ Daily notes: {len(ids)}개 파일 → Qdrant {info.points_count}개")
    return len(ids)


def show_stats():
    """Qdrant 현황"""
    client = get_qdrant()
    print("\n📊 Qdrant Cloud 현황")
    print("=" * 40)
    for col_name in ["long_term_memory", "daily_notes", "echo_memories"]:
        try:
            info = client.get_collection(col_name)
            print(f"  {col_name}: {info.points_count}개")
        except Exception:
            print(f"  {col_name}: (없음)")
    print(f"\n📡 {QDRANT_URL[:50]}...")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "index-memory":
        index_memory_md()
    elif cmd == "index-daily":
        index_daily_notes()
    elif cmd == "index-all":
        print("🔄 전체 인덱싱 시작...")
        index_memory_md()
        index_daily_notes()
        print("\n🎉 완료")
    elif cmd == "stats":
        show_stats()
    else:
        print(f"알 수 없는 명령: {cmd}")
        print("Usage: python3 memory-qdrant.py [index-memory|index-daily|index-all|stats]")
        sys.exit(1)


if __name__ == "__main__":
    main()
