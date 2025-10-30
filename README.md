# 📝 품질기반 SW 설문조사 설계 에이전트

본 에이전트는 SW 품질평가를 위한 설문조사 설계를 자동화하는 AI 기반 지원 시스템입니다.

사용자가 설문조사에 필요한 정보를 입력하면, 
품질 요소를 고려하여 **설문 질문과 측정 메트릭**을 자동으로 생성합니다.

---
## 🎯 프로젝트 개요
### 1. 문제 정의

설문조사 설계 과정에서는 다음과 같은 문제가 발생 가능합니다.

- 담당자의 주관적 판단으로 설문이 구성되어 일관성이 부족하고,
- 중요한 품질 속성에 대한 질문이 누락되거나 유사 질문이 중복되는 현상이 발생합니다.
- 결과적으로 설문에 대해 신뢰할 수 없게 됩니다.

### 2. 타겟 사용자

- 프로젝트 관리자, 품질(QA) 조직, 사업부서, 운영 조직 등


---
## ✨ 주요 기능
### 1) 설문조사 질문 생성 화면
- SW 관련 정보와 LLM을 활용한 질문 생성
- 품질 표준문서를 기반으로 한 질문 검증
- 자동 생성된 질문의 사용자 편집 기능

### 2) 메트릭(Metric) 구성 화면
- LLM을 활용한 평가 척도 생성
- 최종 결과(metric) 문서 생성 및 다운로드 기능

### 3) RAG 데이터 구성 화면
- 문서 업로드 및 인덱싱 기능

---
## 🏗️ 아키텍처
```
내일 클루드에게 문의하기
```

---
## 🛠️ 시스템 구성

```
ms-ai-mvp/
├── app.py                    # 메인 애플리케이션
├── update_data.py            # 데이터 업데이트 스크립트
├── requirements.txt          # Python 패키지 의존성
├── streamlit.sh              # Azure 환경 배포용 Python 패키지 의존성 설치 및 실행 (최초 실행 시 사용)
├── run.sh                    # 로컬에서 Streamlit 실행
├── .env.example              # 환경 변수 템플릿
├── .gitignore                # Git 제외 파일 목록
├── data/
│   └── error_data.json       # 모바일 개통 에러 데이터 (30건, 시스템 상태 포함)
├── test/
│   └── data_test.py          # 테스트 데이터 JSON 포맷 점검
│   └── debug_connection.py   # Azure 연결 테스트
│   └── debug_test.py         # Azure Search 연결 테스트
└── README.md                 # 프로젝트 설명
```

---
## ⚒️ 기술 스택

- Azure OpenAI Service
   - LLM: GPT-4.1-mini (코드 분석 및 가이드 생성)
   - Embedding: text-embedding-ada-002 (벡터 임베딩 생성)
- Azure AI Search: 벡터 검색 인덱스 (코딩 컨벤션, 환경 설정 템플릿)
- Azure Web App: 서비스 배포 및 운영 환경
- Backend: Python 3.11+ (Azure SDK, FastAPI)
- Frontend: Streamlit (웹 UI)
- AI Pipeline: RAG (Retrieval-Augmented Generation)
- Database: Azure AI Search Vector Index

---
### 🌐 배포

#### Azure Web App 배포

**배포 URL**: [🧚‍♂️ BlueBell](https://minseo-web-devpilot-915-a7dvd2h0ckfjcmbh.eastus2-01.azurewebsites.net/) 

### 배포 과정
1. **Azure Web App 생성**: Python 3.11 런타임 설정
2. **환경변수 구성**: Azure Portal에서 앱 설정에 환경변수 추가
3. **VSCode Azure App Service**: VSCode 확장을 통한 배포

---
## ⚙️ 설치 및 설정

### 1. Python 환경 확인
- Python 3.13+ 권장
- pip 패키지 매니저 필요

### 2. 프로젝트 설정

```bash
# 저장소 클론 또는 파일 다운로드
git clone https://github.com/lab1202/ms-ai-mvp.git
cd ms-ai-mvp

# 새 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 환경 변수 파일 생성
cp .env.example .env
# .env 파일을 열어서 Azure 리소스 정보 입력
```bash
# Azure OpenAI 설정
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=
AZURE_OPENAI_API_VERSION=

# Azure Search 설정
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-admin-key-here
AZURE_SEARCH_INDEX_NAME=

# Slack Webhook URL
SLACK_WEBHOOK_URL=

```

## 🚀 시스템 실행

```bash
./streamlit.sh  # 실행 (의존성 생성 포함)
# 의존성 생성이 되어있다면
./run.sh
```

---
### 🔄 향후 개선 

- **LangChain Agent 도입** : 복잡한 코드 분석을 위한 다단계 추론 및 도구 체인 구성
- **파인튜닝 모델 개발** : 실제 사내 코딩 컨벤션 데이터로 모델을 훈련하여 정확도 90% 이상 향상
- **멀티모달 RAG** : 다이어그램, 문서 이미지까지 분석하는 검색 시스템

---



## 개발 고려사항
- LLM 반복 호출 구간의 속도향상을 위한 배치처리 구현
- DB 연결 부담 감소를 위한 DB 반복호출 구간 캐싱 처리

---

## 🔄 SMAF 워크플로우

```
Step1 --> 정보입력 (템플릿 만들어보기)
Step1-1 --> 입력된 정보를 바탕으로 중점 품질요소를 RAG
Step2 --> 질문생성(LLM, RAG)  : 질문생성, 품질속성, 평가지표 (온라인검색기반(최신정보) RAG? 사천구축지식기반RAG?)
Step3 --> 질문조정 및 재생성  : 이중부정, 모호한척도, 복합질문, 유도질문 등 제거 및 조정
Step4 --> 메트릭 정보입력
Step4 --> 메트릭생성(LLM)
Step5 --> 생성결과 확인
Step6 --> 그룹생성 및 가중치 설정(LLM, RAG)
Step7 --> 생성결과 확인
Step8 --> 평가 프레임워크 생성
Step9 --> 결과물 생성(문서생성), 최종 결과 저장하기(추후 불러오기 가능)
```

```
Step1: 도메인 입력 (예: "통신 - 5G")
  ↓
RAG: 도메인별 중점 품질속성 검색
    [여기서 RAG 활용!]
  - 통신: 성능효율성(+++), 신뢰성(+++), 확장성(++)
  ↓
Step2~5: 설문 생성 (이 속성들 중심으로)
  ↓
Step6: 그룹화 및 가중치 설정
  ↓ [여기서 RAG 활용!]
RAG: "통신 도메인에서 성능효율성 가중치는?"
  → 검색 결과: "통신은 성능 35%, 신뢰성 30% 권장"
  ↓
LLM: 도메인 특성 반영한 가중치 제안
```

---
## 할 일

1. 정보입력 항목 세팅 (10.28)
2. RAG 데이터 세팅 (10.28)
3. 질문조정 항목 세팅 (10.28)

비동기 방식 고민해볼 것

플로우 아키텍처를 잘 그려서 AI 한테 이 구조대로 짜달라고 하면 잘 해줌

4단계 모두 LLM 호출이므로, 필요 시 캐싱(st.cache_data)을 활용해 동일 입력에 대해 재요청 방지 가능.

보안강화를 위해 MS Entra ID(Azure AD) 로 db 로그인 적용

Collection Type 이 배포가 안되고 계속 String 으로 들어가는 현상


