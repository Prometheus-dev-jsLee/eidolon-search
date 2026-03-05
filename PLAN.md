# Eidolon Search - Development Plan

## Vision

**"더 큰 벡터 공간이 아니라 더 나은 디코더를 만들어야 한다."**

인간 기억 구조를 모사하는 AI 에이전트 메모리 시스템.

## Architecture

```
의식 레이어 (LLM Context Window)
        ↕
무의식 레이어 (Eidolon Search)
  ├── FTS5 키워드 인덱스 (열쇠)
  ├── 메타데이터 (감정, 시간, 강화)
  ├── 멀티모달 페이로드 (원본)
  └── 백그라운드 프로세스 (망각, 재인덱싱, 클러스터링)
```

## Versions

### v0.0.1 (Released 2026-03-05)
- [x] FTS5 기본 검색
- [x] 90%+ 토큰 절감
- [x] 4개 언어 README
- [x] GitHub + Gitea + ClawHub 배포

### v0.0.2 (Released 2026-03-05)
- [x] Recall 벤치마크
- [x] Cache 벤치마크
- [x] 품질 한계 문서 (QUALITY.md)
- [x] 설치 가이드 3가지
- [x] 샘플 쿼리 예시

### v0.0.3 (dev)
- [x] Alias 사전 (오타/동의어 교정)

### v0.1.0-dev (Current)
- [x] Dual-layer architecture (schema-v2.sql)
- [x] memory_meta 테이블 (valence, arousal, decay_rate, consolidation)
- [x] memory_links 테이블 (기억 간 연결)
- [x] recall_log 테이블 (회상 기록)
- [x] Human-like search (search-v2.py)
- [x] Consolidation process (consolidation.py)
- [x] Re-indexing process (reindex.py)
- [x] Emotional drift (rosy retrospection)
- [x] HTTP API server (api-server.py) — AIRI 연동용
- [x] MEMORY-THEORY.md (논문 기반 설계 문서)

### v0.2.0 (Planned)
- [ ] AIRI memory-eidolon 모듈 통합 테스트
- [ ] Qdrant 벡터 검색 연동 (FTS5 + 벡터 하이브리드)
- [ ] 멀티모달 페이로드 (audio, image paths)
- [ ] 감정 상태 자동 추론 (LLM 기반 valence 태깅)

### v0.3.0 (Future)
- [ ] npm 패키지 배포
- [ ] Trigram fallback (Codex돌쇠 제안: alias 사전 우선)
- [ ] 범용 감각 인코더 연구 (논문 향후 과제)

## AIRI Integration

**포크:** github.com/Prometheus-dev-jsLee/airi
**브랜치:** dev-eidolon-memory
**모듈:** packages/memory-eidolon/

연동 방식:
1. Eidolon API server (Python, port 8384)
2. AIRI memory-eidolon module (TypeScript, HTTP client)
3. "정체성은 중앙에, I/O는 분산으로"

## References

- 논문: `docs/memory-vector-paper.html`
- 설계: `docs/MEMORY-THEORY.md`
- 아키텍처: `docs/architecture/MEMORY-ARCHITECTURE.md`
