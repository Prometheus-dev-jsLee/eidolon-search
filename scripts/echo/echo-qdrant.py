#!/usr/bin/env python3
"""
Echo Qdrant 인덱싱 스크립트
- 매일 작성되는 Echo 회고 (memory/echo-*.md) → Qdrant Cloud
- 자아 유사도 추적, 복리로 쌓이는 기억 시스템
- memory-qdrant.py 구조 참고

Usage:
  python3 echo-qdrant.py index      # Echo 파일들 → Qdrant
  python3 echo-qdrant.py stats      # Qdrant 현황
  python3 echo-qdrant.py similarity # Echo 간 유사도 계산 (TODO)
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


def get_embedder():
    """ChromaDB 내장 임베딩 함수"""
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    return DefaultEmbeddingFunction()


def get_qdrant():
    """Qdrant Cloud 클라이언트"""
    from qdrant_client import QdrantClient
    if not QDRANT_URL:
        raise RuntimeError("QDRANT_URL not set in .env.qdrant")
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=15)


def ensure_collection(client, name: str):
    """컬렉션 존재 확인, 없으면 생성"""
    from qdrant_client.models import VectorParams, Distance, PayloadSchemaType
    try:
        client.get_collection(name)
    except Exception:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"  ✅ 컬렉션 생성: {name}")
    # date 인덱스
    try:
        client.create_payload_index(name, "date",
                                     field_schema=PayloadSchemaType.KEYWORD)
    except Exception:
        pass


def split_by_h2(content: str, source: str = "") -> list[dict]:
    """## 헤더 기준으로 섹션 분리"""
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
    """문자열 ID → uint64 (결정론적 해시)"""
    import hashlib
    return int(hashlib.sha256(text_id.encode()).hexdigest()[:15], 16)


def index_echo_files():
    """Echo 파일들 → Qdrant Cloud"""
    echo_files = sorted(glob.glob(str(MEMORY_DIR / "echo-*.md")))
    
    if not echo_files:
        print("❌ Echo 파일 없음 (memory/echo-*.md)")
        return 0

    ef = get_embedder()
    client = get_qdrant()
    ensure_collection(client, "echo_memories")

    ids, vecs, pays = [], [], []
    total_sections = 0

    for filepath in echo_files:
        filename = os.path.basename(filepath)
        # echo-2026-02-23.md → 2026-02-23
        date_match = re.search(r'echo-(\d{4}-\d{2}-\d{2})', filename)
        if not date_match:
            continue
        date = date_match.group(1)
        
        content = Path(filepath).read_text(encoding="utf-8")
        if len(content) < 100:
            continue

        sections = split_by_h2(content, source=filename)
        total_sections += len(sections)

        for i, section in enumerate(sections):
            doc_id = f"echo-{date}-{i}"
            ids.append(doc_id)
            pays.append({
                "id": doc_id,
                "document": section["content"][:2000],
                "title": section["title"],
                "date": date,
                "source": filename,
                "type": "echo",
                "indexed_at": datetime.now().isoformat(),
            })

    if not ids:
        print("❌ 인덱싱할 섹션 없음")
        return 0

    print(f"📝 {len(echo_files)}개 Echo 파일, {total_sections}개 섹션")

    texts = [p["document"] for p in pays]
    vectors = [v.tolist() for v in ef(texts)]

    upsert_points(client, "echo_memories", ids, vectors, pays)
    info = client.get_collection("echo_memories")
    print(f"✅ Echo 인덱싱 완료: Qdrant {info.points_count}개")
    return len(ids)


def show_stats():
    """Qdrant 현황"""
    client = get_qdrant()
    print("\n📊 Qdrant Cloud - Echo 현황")
    print("=" * 40)
    try:
        info = client.get_collection("echo_memories")
        print(f"  echo_memories: {info.points_count}개")
        
        # 최근 10개 Echo 샘플
        results = client.scroll(
            collection_name="echo_memories",
            limit=10,
            with_payload=True,
            with_vectors=False,
        )
        if results[0]:
            print("\n  최근 Echo:")
            for point in results[0][:5]:
                date = point.payload.get("date", "?")
                title = point.payload.get("title", "?")
                print(f"    - {date}: {title[:40]}")
    except Exception as e:
        print(f"  echo_memories: (없음 또는 오류: {e})")
    print(f"\n📡 {QDRANT_URL[:50]}...")


def calc_similarity():
    """Echo 간 유사도 계산 (TODO)"""
    print("\n🔮 Echo 유사도 계산 (미구현)")
    print("=" * 40)
    print("  TODO: 오늘의 Echo vs 이전 Echo 유사도")
    print("  TODO: 시간에 따른 자아 변화 추적")
    print("  TODO: 가장 일관된 섹션 vs 가장 변화한 섹션")
    return


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "index":
        index_echo_files()
    elif cmd == "stats":
        show_stats()
    elif cmd == "similarity":
        calc_similarity()
    else:
        print(f"알 수 없는 명령: {cmd}")
        print("Usage: python3 echo-qdrant.py [index|stats|similarity]")
        sys.exit(1)


if __name__ == "__main__":
    main()
