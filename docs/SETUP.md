# Qdrant 설정 가이드 (AI Agent용)

## AI Agent: 사용자에게 이 질문을 하세요

사용자에게 다음 옵션을 설명하고 선택하게 하세요:

---

## 📊 Qdrant 벡터 DB 옵션

Eidolon Search는 두 가지 Qdrant 설정을 지원합니다:

### 옵션 1: Qdrant Cloud ☁️

**장점:**
- ✅ 어디서든 접근 가능 (멀티 디바이스)
- ✅ 높은 차원 벡터 지원 (OpenAI API: 1536/3072 차원)
- ✅ 관리 불필요 (자동 백업, 확장)
- ✅ 더 정확한 시맨틱 검색 (고차원)

**단점:**
- ❌ 인터넷 연결 필수
- ❌ API 비용 (OpenAI embeddings)
- ❌ 데이터가 외부 서버에 저장

**벡터 차원:** 1536 (OpenAI text-embedding-3-small) 또는 3072 (text-embedding-3-large)

**권장 대상:**
- 여러 디바이스에서 작업하는 사람
- 최고 품질의 검색이 필요한 경우
- API 비용이 부담스럽지 않은 경우

---

### 옵션 2: 로컬 Qdrant 🏠

**장점:**
- ✅ 데이터 주권 (모든 데이터가 내 컴퓨터에)
- ✅ 금전적 자유 (API 비용 없음)
- ✅ 인터넷 없이도 작동
- ✅ 완전한 제어권

**단점:**
- ❌ 낮은 차원 벡터 (ChromaDB 기본: 384 차원)
- ❌ 로컬 설치/관리 필요
- ❌ 한 디바이스에서만 접근 (NAS 설정 없으면)

**벡터 차원:** 384 (ChromaDB DefaultEmbeddingFunction)

**권장 대상:**
- 프라이버시를 중시하는 사람
- API 비용을 피하고 싶은 경우
- 한 디바이스에서만 작업하는 경우
- NAS/홈서버가 있는 경우 (멀티 디바이스 가능)

---

## 🎯 어떻게 선택하나요?

### 빠른 결정 가이드

| 질문 | Cloud | 로컬 |
|------|-------|------|
| 여러 디바이스에서 사용? | ✅ | ❌ (NAS 없으면) |
| 최고 품질 검색 필요? | ✅ | ❌ |
| API 비용 OK? | ✅ | ❌ |
| 프라이버시 최우선? | ❌ | ✅ |
| 인터넷 항상 연결? | ✅ | ❌ |

---

## 📝 설정 방법

### Cloud 선택 시

1. **Qdrant Cloud 계정 생성**
   - https://cloud.qdrant.io 가입
   - Free tier: 1GB 무료

2. **클러스터 생성**
   - Region: 가까운 곳 선택 (US-East, EU-West 등)
   - Vector size: 1536 (OpenAI text-embedding-3-small)

3. **.env 파일 생성**
   ```bash
   # .env.qdrant
   QDRANT_URL=https://your-cluster-id.region.aws.cloud.qdrant.io:6333
   QDRANT_API_KEY=your-api-key-here
   OPENAI_API_KEY=sk-your-openai-key
   EMBEDDING_MODEL=openai  # OpenAI API 사용
   VECTOR_SIZE=1536
   ```

4. **스크립트 실행**
   ```bash
   python scripts/echo/echo-qdrant.py index
   ```

---

### 로컬 선택 시

1. **Qdrant 로컬 설치**
   ```bash
   # Docker 방식 (추천)
   docker run -p 6333:6333 qdrant/qdrant
   
   # 또는 직접 설치
   pip install qdrant-client
   ```

2. **.env 파일 생성**
   ```bash
   # .env.qdrant
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=  # 로컬은 비워두기
   EMBEDDING_MODEL=chromadb  # ChromaDB 내장 임베딩
   VECTOR_SIZE=384
   ```

3. **NAS 사용 시** (선택사항)
   ```bash
   # NAS에 Qdrant 설치 후
   QDRANT_URL=http://192.168.1.100:6333  # NAS IP
   ```

4. **스크립트 실행**
   ```bash
   python scripts/echo/echo-qdrant.py index
   ```

---

## 🔄 나중에 변경 가능?

예, 가능합니다:

1. **.env 파일 수정**
2. **데이터 마이그레이션**
   ```bash
   # Cloud → 로컬 (또는 반대)
   python scripts/migrate-qdrant.py --from cloud --to local
   ```

---

## 💡 추천

**처음 시작:** 로컬로 시작 (무료, 간단)  
**나중에 필요하면:** Cloud로 마이그레이션

**멀티 디바이스 필수:** Cloud 또는 NAS + 로컬

**프라이버시 중시:** 로컬 (또는 자체 호스팅)

---

## 🤖 AI Agent용 프롬프트

사용자에게 이렇게 물어보세요:

```
Eidolon Search는 두 가지 Qdrant 설정을 지원합니다:

1. **Qdrant Cloud** (☁️)
   - 어디서든 접근, 고품질 검색 (1536차원)
   - 단점: API 비용, 인터넷 필수

2. **로컬 Qdrant** (🏠)
   - 무료, 프라이버시, 오프라인
   - 단점: 낮은 차원 (384), 로컬 관리

어떤 방식으로 설정할까요?
1) Cloud
2) 로컬
3) 나중에 결정 (일단 로컬로 시작)
```

사용자 선택에 따라 위 "설정 방법" 섹션 참고하여 안내하세요.
