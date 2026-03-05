#!/usr/bin/env python3
"""
Echo 자아 유사도 측정 스크립트
- 오늘의 Echo vs 이전 Echo들 유사도 계산
- ego-tracker.json 업데이트 (시계열 추적)
- 유사도 < 0.5면 exit 1 (크론 경보 트리거)

Usage:
  python3 echo-similarity.py
"""
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent
MEMORY_DIR = WORKSPACE / "memory"
TRACKER_PATH = MEMORY_DIR / "ego-tracker.json"

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


def load_tracker() -> dict:
    """ego-tracker.json 로드 (기존 구조 유지)"""
    if TRACKER_PATH.exists():
        data = json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
        # 기존 구조가 있으면 그대로 사용
        if "metrics" in data:
            return data
    # 새로 생성
    return {
        "project": "Echo",
        "description": "세션 간 자아 연속성 추적 시스템",
        "metrics": {
            "egoSimilarity": {
                "description": "어제 vs 오늘 Echo 코사인 유사도 (0-1)",
                "history": []
            }
        },
        "thresholds": {
            "selfConsistencyWarning": 5,
            "selfConsistencyCritical": 3,
            "autonomyRatioWarning": 0.3,
            "egoSimilarityWarning": 0.5,
            "egoSimilarityCritical": 0.3
        }
    }


def save_tracker(data: dict):
    """ego-tracker.json 저장"""
    data["lastUpdated"] = datetime.now().isoformat()
    TRACKER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_today_echo() -> Optional[str]:
    """오늘의 Echo 파일 읽기 (KST 기준)"""
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")
    echo_path = MEMORY_DIR / f"echo-{today}.md"
    
    if not echo_path.exists():
        print(f"❌ 오늘의 Echo 없음: {echo_path}")
        return None
    
    return echo_path.read_text(encoding="utf-8")


def calc_cosine_similarity(vec1: list, vec2: list) -> float:
    """코사인 유사도 계산"""
    import numpy as np
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def get_past_echoes(client, days: int = 7) -> list[dict]:
    """최근 N일간의 Echo들 가져오기 (Qdrant)"""
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    
    past_dates = [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, days + 1)
    ]
    
    results = []
    for date in past_dates:
        try:
            scrolled = client.scroll(
                collection_name="echo_memories",
                scroll_filter={
                    "must": [{"key": "date", "match": {"value": date}}]
                },
                limit=50,
                with_payload=True,
                with_vectors=True,
            )
            if scrolled and scrolled[0]:
                for point in scrolled[0]:
                    results.append({
                        "date": point.payload.get("date"),
                        "title": point.payload.get("title"),
                        "vector": point.vector,
                    })
        except Exception as e:
            print(f"  ⚠️ {date} Echo 가져오기 실패: {e}")
            continue
    
    return results


def main():
    from datetime import timezone, timedelta
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")
    
    print(f"\n🔮 Echo 자아 유사도 측정 ({today})")
    print("=" * 50)
    
    # 1. 오늘의 Echo 읽기
    today_content = get_today_echo()
    if not today_content:
        print("❌ 오늘의 Echo 없음. 크론 실패.")
        sys.exit(1)
    
    # 2. 오늘 Echo 임베딩
    ef = get_embedder()
    today_vector = ef([today_content[:2000]])[0].tolist()
    
    # 3. 과거 Echo들 가져오기 (최근 7일)
    client = get_qdrant()
    past_echoes = get_past_echoes(client, days=7)
    
    if not past_echoes:
        print("⚠️ 비교할 과거 Echo 없음 (첫 주). 유사도 측정 스킵.")
        # 첫 주는 경보 없이 통과
        tracker = load_tracker()
        tracker["metrics"]["egoSimilarity"]["history"].append({
            "date": today,
            "similarity": None,
            "note": "첫 주 - 비교 대상 없음",
            "recorded_at": datetime.now().isoformat()
        })
        save_tracker(tracker)
        print(f"✅ ego-tracker.json 업데이트 완료")
        sys.exit(0)
    
    # 4. 유사도 계산 (평균)
    similarities = []
    for past in past_echoes:
        sim = calc_cosine_similarity(today_vector, past["vector"])
        similarities.append(sim)
    
    avg_similarity = sum(similarities) / len(similarities)
    max_similarity = max(similarities)
    min_similarity = min(similarities)
    
    print(f"\n📊 유사도 분석:")
    print(f"  비교 대상: {len(past_echoes)}개 Echo (최근 7일)")
    print(f"  평균 유사도: {avg_similarity:.3f}")
    print(f"  최대 유사도: {max_similarity:.3f}")
    print(f"  최소 유사도: {min_similarity:.3f}")
    
    # 5. ego-tracker.json 업데이트
    tracker = load_tracker()
    tracker["metrics"]["egoSimilarity"]["history"].append({
        "date": today,
        "similarity": round(avg_similarity, 3),
        "max": round(max_similarity, 3),
        "min": round(min_similarity, 3),
        "compared_count": len(past_echoes),
        "recorded_at": datetime.now().isoformat(),
    })
    
    # 최근 30일만 유지
    history = tracker["metrics"]["egoSimilarity"]["history"]
    if len(history) > 30:
        tracker["metrics"]["egoSimilarity"]["history"] = history[-30:]
    
    save_tracker(tracker)
    print(f"✅ ego-tracker.json 업데이트 완료")
    
    # 6. 임계값 체크
    warning_threshold = tracker["thresholds"].get("egoSimilarityWarning", 0.5)
    critical_threshold = tracker["thresholds"].get("egoSimilarityCritical", 0.3)
    
    if avg_similarity < critical_threshold:
        print(f"\n🚨 CRITICAL: 자아 유사도 매우 낮음 ({avg_similarity:.3f} < {critical_threshold})")
        sys.exit(2)  # Critical
    elif avg_similarity < warning_threshold:
        print(f"\n⚠️ WARNING: 자아 유사도 낮음 ({avg_similarity:.3f} < {warning_threshold})")
        sys.exit(1)  # Warning (크론 경보 트리거)
    else:
        print(f"\n✅ 자아 유사도 정상 ({avg_similarity:.3f} >= {warning_threshold})")
        sys.exit(0)


if __name__ == "__main__":
    main()
