# 📝 품질기반 SW 설문조사 설계 에이전트

본 에이전트는 SW 품질평가를 위한 설문조사 설계를 자동화하는 AI 기반 지원 시스템입니다.

사용자가 설문조사에 필요한 정보를 입력하면, 
품질 요소를 고려하여 **설문 질문과 측정 메트릭**을 자동으로 생성합니다.


접속 URL : [설문조사 설계 시작!](https://pro-wonka-web-cec5hhfxdmfsdhe3.polandcentral-01.azurewebsites.net)

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
## 📌 주요 기능
### 1) 설문조사 설계
- ISO 25010 품질표준 기반으로 LLM 을 통한 설문조사의 질문생성 및 메트릭 구성
- 설문조사 메트릭 문서 다운로드

### 2) RAG 기반 설문 검증
- Azure AI Search를 이용해 LLM 이 자동생성한 질문에 대한 품질속성의 적절성 검증
- 문서 업로드 및 인덱싱을 위한 UI 지원

### 3) 웹 어플리케이션
- Streamlit 웹 UI 구성 및 데이터베이스를 활용한 웹 어플리케이션

---
## 🔄 워크플로우

```
Step1: SW 정보입력 및 질문생성 버튼 클릭!
  ↓
Step2: LLM 을 통한 질문 생성
  ↓     
      1. 입력정보를 통한 SW분석
      2. 주요 품질속성 선정
      3. 품질 속성에 맞는 질문 생성 ( ex. [기능 적합성] 결제 과정이 문제없이 진행되어 구매를 완료할 수 있습니까? )
      4. 생성된 질문에 대한 품질속성을 RAG를 통해 재분류
      5. 문제항목 최종검토 (중복, 유도질문, 이중부정, 모호한척도)
      6. 최종 질문선정
  ↓
Step3: 생성된 질문에 대한 사용자 커스터마이징
  ↓
Step4: 평가척도 선택 및 메트릭 생성
  ↓
Step5: 설문 생성결과 확인

```

---
## 🛠️ 시스템 구성

```
ms-ai-mvp
├── app.py                        # 메인 애플리케이션(설문조사 생성기)
├── data
│   ├── convert_iso25010.py       # 문서를 index 구조로 변환하는 스크립트
│   ├── create_index.py           # index 생성 스크립트
│   ├── iso25010_documents.json   # 변환된 문서
│   ├── ISO25010.txt              # 원본 문서(ISO25010 품질문서)
│   └── upload_data.py            # 데이터 업로드 스크립트
├── db
│   ├── create_tables.py          # Postgres Table 생성 스크립트
│   └── schema.sql                # 테이블 스키마
├── test
│   ├── test_db_connection.py     # Database 연결 테스트
│   └── test_vector.py            # Vector 검색 테스트
├── .gitignore                    # Git 제외 파일 목록
├── iso25010_rag.py               # UI(1/3) : 문서 업로드 및 인덱스 생성 화면
├── survey_gen.py                 # UI(2/3) : 설문조사 질문을 생성하는 화면
├── metric_gen.py                 # UI(3/3) : 설문조사 메트릭을 생성하는 화면
├── README.md                     # 프로젝트 설명
├── requirements.txt              # Python 패키지 의존성
└── setup.sh                      # uv 가상환경 및 라이브러리 구성 스크립트
```

---
## ⚒️ Azure 기술 스택

- Azure OpenAI
   - LLM: GPT-4.1-mini
   - Embedding: text-embedding-3-short
- Azure AI Search
- Azure Web App
- Frontend: Streamlit (웹 UI)
- AI Pipeline: LLM + RAG
- Database: Postgres

---
## 💡 개발시 고려한 내용
- 정확한 RAG 처리를 위한 인덱스 스키마 구성
- LLM 반복 호출 구간의 속도향상을 위한 배치처리
- DB 반복 호출 부담 감소를 위한 캐싱 처리
- 확장성을 고려한 데이터베이스 테이블 설계
