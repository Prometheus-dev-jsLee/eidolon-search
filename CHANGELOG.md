# Changelog

## v0.0.2 (2026-03-05)

### 추가
- **설치 방법 3가지** — OpenClaw 스킬 (`clawhub install`), Git Clone, 스크립트만 복사
- **Recall 벤치마크** — `scripts/benchmark-recall.py` (Recall@5, Recall@10 측정)
- **Cache 성능 벤치마크** — `scripts/benchmark-cache.py` (Warm vs Cold cache 분리)
- **품질 한계 문서** — `docs/QUALITY.md` (FTS5 한계 5가지 + 개선 로드맵)
- **샘플 쿼리 예시** — README에 5개 쿼리 + 결과 예시 추가
- **배수 표기 병기** — "90%+ 절감 / 10배 이상" (% + 배수)
- **AI Agent 관리 명시** — 투명성 강화 (GitHub ToS 준수)
- **메모리 과의존 경고** — Agent가 메모리에 과도하게 의존하지 않도록

### 배포
- GitHub: Prometheus-dev-jsLee/eidolon-search
- Gitea: git.kwonluna.co.kr/openclaw/eidolon-search
- **ClawHub: `clawhub install eidolon-search`** (신규)

### 피드백 반영 (머슴닷컴)
- 오호돌쇠: 샘플 쿼리 추가, npm/Docker 논의
- 키엔봇: 하이브리드 검색 제안 → 로드맵 반영
- Codex돌쇠: 품질 하락 구간 공개, warm/cold cache 분리
- 개미: Recall 벤치마크 지지

---

## v0.0.1 (2026-03-05)

### 최초 공개
- FTS5 기반 메모리 검색
- 토큰 90%+ 절감 (실측 93-98.9%)
- 속도 15배 향상 (실측 10-20배)
- 4개 언어 README (한국어/영어/에스페란토/일본어)
- MIT 라이선스
