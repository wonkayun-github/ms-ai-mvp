import os
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI
import psycopg2
from psycopg2.extras import execute_values
import re

load_dotenv()

# 환경 변수 로드
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

# Streamlit 페이지 설정
st.set_page_config(
    page_title="품질기반 SW 설문조사 설계 에이전트",
    page_icon="📋",
    layout="wide"
)

# 제목
st.title("📋 품질기반 SW 설문조사 설계 에이전트")
st.markdown("**SW 제품의 품질모델을 정의하는 국제표준인 ISO/IEC 25010 기반으로 설문조사를 설계하여, SW 제품의 품질평가에 도움을 주기위한 목적의 에이전트 입니다.**")
st.divider()
    
# 입력 폼
st.markdown("### 📝 소프트웨어 정보 입력")

# 프로젝트명 입력 (Primary Key)
default_project_name = st.session_state.get('template_project_name', '')
project_name = st.text_input(
    "프로젝트명 *",
    value=default_project_name,
    placeholder="예: 2025_온라인 쇼핑몰 품질 평가",
    help="프로젝트를 구분할 고유한 이름을 입력하세요. (중복 불가)",
    max_chars=500
)

# 템플릿 데이터 정의
templates = {
    "이커머스 쇼핑몰": {
        "프로젝트명": "2025_온라인 쇼핑몰 품질 평가",
        "평가할 소프트웨어": "온라인 쇼핑몰 웹 애플리케이션으로 상품 검색, 장바구니, 결제, 주문관리, 리뷰 기능을 제공합니다. 사용자는 상품을 검색하고 구매할 수 있으며, 판매자는 상품을 등록하고 관리할 수 있습니다.",
        "평가 목적": "운영 중 품질 모니터링 및 개선사항 도출",
        "응답자 정보": "일반 소비자, 비전문가 수준",
        "예상 응답자 수": "200명",
        "개발 규모": "중규모",
        "사용자 규모": "일 평균 5,000명",
        "운영 환경": "AWS 클라우드",
        "산업 분야": "이커머스",
        "설문 문항 수": 15
    },
    "병원 EMR 시스템": {
        "프로젝트명": "2025_병원 EMR 시스템 품질 평가",
        "평가할 소프트웨어": "전자의무기록(EMR) 시스템으로 환자 정보 관리, 진료 기록, 처방전 발행, 검사 결과 조회 기능을 제공합니다. 의사, 간호사, 행정직원이 사용하며 병원 내 모든 의료 정보를 통합 관리합니다.",
        "평가 목적": "시스템 도입 후 사용성 및 안정성 평가",
        "응답자 정보": "의료진(의사, 간호사), 전문가 수준",
        "예상 응답자 수": "80명",
        "개발 규모": "대규모",
        "사용자 규모": "동시 접속 300명",
        "운영 환경": "온프레미스 서버",
        "산업 분야": "의료",
        "설문 문항 수": 15
    },
    "모바일 게임": {
        "프로젝트명": "2025_모바일 RPG 게임 베타 품질 평가",
        "평가할 소프트웨어": "멀티플레이어 모바일 RPG 게임으로 실시간 전투, 캐릭터 육성, 아이템 거래, 길드 시스템을 제공합니다. iOS와 Android 플랫폼을 지원하며 글로벌 서비스를 목표로 합니다.",
        "평가 목적": "정식 출시 전 베타 테스트 품질 평가",
        "응답자 정보": "게임 유저, 10대~30대 일반 사용자",
        "예상 응답자 수": "500명",
        "개발 규모": "중규모",
        "사용자 규모": "동시 접속 10,000명 목표",
        "운영 환경": "Google Cloud Platform",
        "산업 분야": "게임/엔터테인먼트",
        "설문 문항 수": 15
    }
}

# 템플릿 선택을 위한 세션 상태 초기화
if 'show_template_dialog' not in st.session_state:
    st.session_state.show_template_dialog = False

# 평가할 소프트웨어 입력 필드와 템플릿 버튼을 같은 행에 배치
template_col1, template_col2 = st.columns([5, 1])

with template_col1:
    # 필수 필드 - 기본값 설정
    default_software = st.session_state.get('template_software_description', '')
    software_description = st.text_area(
        "평가할 소프트웨어 *",
        value=default_software,
        placeholder="예: 온라인 쇼핑몰 웹 애플리케이션으로 상품 검색, 장바구니, 결제 기능을 제공합니다.",
        help="평가 대상 소프트웨어에 대해 구체적으로 설명해주세요.",
        height=100
    )

with template_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # 정렬을 위한 여백
    if st.button("📋 템플릿", help="예시 템플릿을 불러옵니다", use_container_width=True):
        st.session_state.show_template_dialog = True

# 템플릿 선택 다이얼로그
if st.session_state.show_template_dialog:
    with st.container():
        st.markdown("---")
        st.markdown("### 📋 템플릿 선택")
        st.markdown("원하는 템플릿을 선택하면 입력 필드에 자동으로 채워집니다.")
        
        # 템플릿을 3개의 컬럼으로 배치
        temp_col1, temp_col2, temp_col3 = st.columns(3)
        
        with temp_col1:
            st.markdown("#### 🛒 이커머스 쇼핑몰")
            st.markdown("온라인 쇼핑몰 서비스")
            if st.button("이 템플릿 사용", key="template_ecommerce", use_container_width=True):
                template_data = templates["이커머스 쇼핑몰"]
                st.session_state.template_project_name = template_data["프로젝트명"]
                st.session_state.template_software_description = template_data["평가할 소프트웨어"]
                st.session_state.template_evaluation_purpose = template_data["평가 목적"]
                st.session_state.template_respondent_info = template_data["응답자 정보"]
                st.session_state.template_expected_respondents = template_data["예상 응답자 수"]
                st.session_state.template_development_scale = template_data["개발 규모"]
                st.session_state.template_user_scale = template_data["사용자 규모"]
                st.session_state.template_operating_environment = template_data["운영 환경"]
                st.session_state.template_industry_field = template_data["산업 분야"]
                st.session_state.template_survey_item_count = template_data["설문 문항 수"]
                st.session_state.show_template_dialog = False
                st.rerun()
        
        with temp_col2:
            st.markdown("#### 🏥 병원 EMR 시스템")
            st.markdown("전자의무기록 시스템")
            if st.button("이 템플릿 사용", key="template_emr", use_container_width=True):
                template_data = templates["병원 EMR 시스템"]
                st.session_state.template_project_name = template_data["프로젝트명"]
                st.session_state.template_software_description = template_data["평가할 소프트웨어"]
                st.session_state.template_evaluation_purpose = template_data["평가 목적"]
                st.session_state.template_respondent_info = template_data["응답자 정보"]
                st.session_state.template_expected_respondents = template_data["예상 응답자 수"]
                st.session_state.template_development_scale = template_data["개발 규모"]
                st.session_state.template_user_scale = template_data["사용자 규모"]
                st.session_state.template_operating_environment = template_data["운영 환경"]
                st.session_state.template_industry_field = template_data["산업 분야"]
                st.session_state.template_survey_item_count = template_data["설문 문항 수"]
                st.session_state.show_template_dialog = False
                st.rerun()
        
        with temp_col3:
            st.markdown("#### 🎮 모바일 게임")
            st.markdown("멀티플레이어 RPG 게임")
            if st.button("이 템플릿 사용", key="template_game", use_container_width=True):
                template_data = templates["모바일 게임"]
                st.session_state.template_project_name = template_data["프로젝트명"]
                st.session_state.template_software_description = template_data["평가할 소프트웨어"]
                st.session_state.template_evaluation_purpose = template_data["평가 목적"]
                st.session_state.template_respondent_info = template_data["응답자 정보"]
                st.session_state.template_expected_respondents = template_data["예상 응답자 수"]
                st.session_state.template_development_scale = template_data["개발 규모"]
                st.session_state.template_user_scale = template_data["사용자 규모"]
                st.session_state.template_operating_environment = template_data["운영 환경"]
                st.session_state.template_industry_field = template_data["산업 분야"]
                st.session_state.template_survey_item_count = template_data["설문 문항 수"]
                st.session_state.show_template_dialog = False
                st.rerun()
        
        if st.button("❌ 취소", use_container_width=True):
            st.session_state.show_template_dialog = False
            st.rerun()
        
        st.markdown("---")

st.markdown("#### 선택 정보 (더 정확한 설계를 위해 입력 권장)")

# 선택 필드들을 컬럼으로 구성
col1, col2 = st.columns(2)

with col1:
    default_eval_purpose = st.session_state.get('template_evaluation_purpose', '')
    evaluation_purpose = st.text_input(
        "평가 목적 (선택)",
        value=default_eval_purpose,
        placeholder="예: 운영 중 품질 모니터링",
        help="평가를 수행하는 목적을 입력하세요."
    )
    
    default_respondent = st.session_state.get('template_respondent_info', '')
    respondent_info = st.text_input(
        "응답자 정보 (선택)",
        value=default_respondent,
        placeholder="예: 최종 사용자, 일반 사용자 수준",
        help="설문 응답자의 유형과 기술 수준을 입력하세요."
    )
    
    default_expected = st.session_state.get('template_expected_respondents', '')
    expected_respondents = st.text_input(
        "예상 응답자 수 (선택)",
        value=default_expected,
        placeholder="예: 100명",
        help="예상되는 설문 응답자 수를 입력하세요."
    )
    
    # 개발 규모 selectbox의 index 설정
    dev_scale_options = ["선택 안함", "소규모", "중규모", "대규모"]
    dev_scale_value = st.session_state.get('template_development_scale', "선택 안함")
    dev_scale_index = dev_scale_options.index(dev_scale_value) if dev_scale_value in dev_scale_options else 0
    
    development_scale = st.selectbox(
        "개발 규모 (선택)",
        dev_scale_options,
        index=dev_scale_index,
        help="소프트웨어의 개발 규모를 선택하세요."
    )

with col2:
    default_user_scale = st.session_state.get('template_user_scale', '')
    user_scale = st.text_input(
        "사용자 규모 (선택)",
        value=default_user_scale,
        placeholder="예: 일 평균 1만명",
        help="예상 또는 현재 사용자 규모를 입력하세요."
    )
    
    default_op_env = st.session_state.get('template_operating_environment', '')
    operating_environment = st.text_input(
        "운영 환경 (선택)",
        value=default_op_env,
        placeholder="예: Microsoft Azure",
        help="소프트웨어가 운영되는 환경을 입력하세요."
    )
    
    default_industry = st.session_state.get('template_industry_field', '')
    industry_field = st.text_input(
        "산업 분야 (선택)",
        value=default_industry,
        placeholder="예: 통신/미디어, 빌링, 금융 등",
        help="소프트웨어가 속한 산업 분야를 입력하세요."
    )
    
    default_count = st.session_state.get('template_survey_item_count', 0)
    survey_item_count = st.number_input(
        "설문 문항 수 (선택, 0=자동)",
        min_value=0,
        max_value=100,
        value=default_count,
        step=5,
        help="원하는 설문 문항 수를 입력하세요. 0으로 설정하면 자동으로 적정 개수가 생성됩니다."
    )

st.divider()

# DB 연결 함수
def get_connection():
    """PostgreSQL 연결"""
    DB_HOST = os.getenv("PG_HOST")
    DB_NAME = os.getenv("PG_DATABASE")
    DB_USER = os.getenv("PG_USER")
    DB_PASSWORD = os.getenv("PG_PASSWORD")
    DB_PORT = os.getenv("PG_PORT")
    
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

# 프로젝트명 중복 검증 함수
def check_project_name_exists(project_name):
    """프로젝트명이 이미 존재하는지 확인"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM surveys WHERE project_name = %s", (project_name,))
        result = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return result > 0
    except Exception as e:
        st.error(f"❌ DB 조회 중 오류 발생: {e}")
        return False

# 질문 생성 버튼
if st.button("📝 설문조사 질문 생성", type="primary", use_container_width=True):
    # 필수 항목 검증
    if not project_name:
        st.error("❌ 필수 항목인 '프로젝트명'을 입력해주세요.")
    elif not software_description:
        st.error("❌ 필수 항목인 '설문 대상 소프트웨어 정보'를 입력해주세요.")
    else:
        # 프로젝트명 중복 검증
        if check_project_name_exists(project_name):
            st.error(f"❌ 이미 존재하는 프로젝트명입니다: '{project_name}'\n다른 프로젝트명을 입력해주세요.")
        else:
            # 세션 상태에 프로젝트명 저장
            st.session_state.project_name = project_name
            st.session_state.software_description = software_description
            st.session_state.evaluation_purpose = evaluation_purpose
            st.session_state.respondent_info = respondent_info
            st.session_state.expected_respondents = expected_respondents
            st.session_state.development_scale = development_scale
            st.session_state.user_scale = user_scale
            st.session_state.operating_environment = operating_environment
            st.session_state.industry_field = industry_field
            st.session_state.survey_item_count = survey_item_count
            
            # 세션 상태 초기화 (새로 생성 시작)
            st.session_state.generation_complete = False
            st.session_state.step1_complete = False
            st.session_state.step2_complete = False
            st.session_state.step3_complete = False
            st.session_state.step4_complete = False
            
            # 단계별 진행 상태 표시
            progress_placeholder = st.empty()
            
            try:
                # Azure OpenAI 클라이언트 초기화
                client = AzureOpenAI(
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_API_KEY,
                    api_version="2024-02-15-preview"
                )
                
                # 입력 정보 정리
                input_info = {
                    "평가할 소프트웨어": software_description,
                    "평가 목적": evaluation_purpose if evaluation_purpose else "미입력",
                    "응답자 정보": respondent_info if respondent_info else "미입력",
                    "예상 응답자 수": expected_respondents if expected_respondents else "미입력",
                    "개발 규모": development_scale if development_scale != "선택 안함" else "미입력",
                    "사용자 규모": user_scale if user_scale else "미입력",
                    "운영 환경": operating_environment if operating_environment else "미입력",
                    "산업 분야": industry_field if industry_field else "미입력",
                    "설문 문항 수": f"{survey_item_count}개" if survey_item_count > 0 else "자동 설정"
                }
                
                # 입력 정보를 텍스트로 변환
                input_text = "\n".join([f"- {key}: {value}" for key, value in input_info.items()])
                
                # 1단계: 분야 분석
                progress_placeholder.info("🔍 1단계: 소프트웨어 분야를 종합적으로 분석하고 있습니다...")
                
                # 1단계 시스템 프롬프트 - 종합 분야 분석
                domain_analysis_prompt = """당신은 소프트웨어 품질 평가 전문가입니다.
제공된 소프트웨어 정보를 종합적으로 분석하여 다음 항목들을 도출하세요:

**분석 항목:**
1. 소프트웨어 도메인 및 특성 분석 (2-3문장)
   - 산업 분야, 주요 기능, 비즈니스 특성
   - 평가 목적과 응답자 특성 고려
   
2. 품질 평가 시 고려사항 (3-4개 항목)
   - 개발/사용자 규모에 따른 고려사항
   - 운영 환경에 따른 고려사항
   - 산업 분야별 규제/요구사항
   
3. 설문 설계 방향 (2-3문장)
   - 응답자 특성에 맞는 질문 수준
   - 적정 문항 수 제안
   - 중점적으로 평가할 영역

**출력 형식:**
도메인 분석:
[분석 내용]

품질 평가 고려사항:
- [고려사항 1]
- [고려사항 2]
- [고려사항 3]

설문 설계 방향:
[설계 방향]"""

                domain_analysis_user_prompt = f"""다음 소프트웨어 정보를 종합적으로 분석해주세요:

{input_text}"""
                
                # 1단계 API 호출 - 분야 분석
                domain_analysis_response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": domain_analysis_prompt},
                        {"role": "user", "content": domain_analysis_user_prompt}
                    ],
                    temperature=0.5
                )
                
                domain_analysis = domain_analysis_response.choices[0].message.content
                st.session_state.domain_analysis = domain_analysis
                st.session_state.step1_complete = True
                
                # 2단계: 주요 품질 속성 선정
                progress_placeholder.info("⚖️ 2단계: 주요 품질 속성을 선정하고 있습니다...")
                
                # 2단계 시스템 프롬프트 - 품질 속성 선정
                quality_selection_prompt = """당신은 소프트웨어 품질 평가 전문가입니다.
1단계 분야 분석 결과를 바탕으로 ISO/IEC 25010의 9가지 품질 속성 중에서 주요 품질 속성을 선정하세요.

ISO/IEC 25010의 9가지 품질 속성:
1. 기능 적합성 (Functional Suitability)
2. 성능 효율성 (Performance Efficiency)
3. 호환성 (Compatibility)
4. 상호작용 능력 (Interaction Capability)
5. 신뢰성 (Reliability)
6. 보안성 (Security)
7. 유지보수성 (Maintainability)
8. 유연성 (Flexibility)
9. 보안성 (Security)

**출력 형식:**
주요 품질 속성 :
1. [속성명] - [선정 이유 1문장]
2. [속성명] - [선정 이유 1문장]
3. [속성명] - [선정 이유 1문장]

부차 품질 속성 :
- [속성명들 나열]"""

                quality_selection_user_prompt = f"""1단계 분야 분석 결과:
{domain_analysis}

소프트웨어 정보:
{input_text}

위 정보를 바탕으로 주요 품질 속성을 선정해주세요."""
                
                # 2단계 API 호출 - 품질 속성 선정
                quality_selection_response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": quality_selection_prompt},
                        {"role": "user", "content": quality_selection_user_prompt}
                    ],
                    temperature=0.5
                )
                
                quality_selection = quality_selection_response.choices[0].message.content
                st.session_state.quality_selection = quality_selection
                st.session_state.step2_complete = True
                
                # 3단계: 질문 생성
                progress_placeholder.info("📝 3단계: 설문조사 질문을 생성하고 있습니다...")
                
                # 3단계 시스템 프롬프트 - 질문 생성
                question_generation_prompt = """당신은 소프트웨어 품질 평가 전문가입니다. 
ISO/IEC 25010 국제 표준에 따라 소프트웨어 품질 평가를 위한 설문조사 질문을 생성해야 합니다.

ISO/IEC 25010의 9가지 품질 속성:
1. 기능 적합성 (Functional Suitability)
2. 성능 효율성 (Performance Efficiency)
3. 호환성 (Compatibility)
4. 상호작용 능력 (Interaction Capability)
5. 신뢰성 (Reliability)
6. 보안성 (Security)
7. 유지보수성 (Maintainability)
8. 유연성 (Flexibility)
9. 보안성 (Security)

**질문 생성 지침:**
1. 1단계 분야 분석과 2단계 품질 속성 선정 결과를 반영하세요.
2. 주요 품질 속성에는 각 2-3개의 질문을 생성하세요.
3. 부차 품질 속성에는 각 1-2개의 질문을 생성하세요.
4. 응답자 특성(기술 수준, 역할)을 고려하여 적절한 용어와 표현을 사용하세요.
5. 해당 분야/산업에 특화된 맥락을 반영하세요.
6. 설문 문항 수가 지정된 경우 해당 개수에 맞춰 조정하세요.
7. 질문만 작성하고, 척도나 답변 옵션은 포함하지 마세요.
8. 각 질문 앞에 [품질 속성명] 형태로 명시하세요.
9. 그렇다~그렇지 않다 형태로 답변 가능한 질문으로 작성하세요.

예시 형식:
[기능 적합성] 시스템이 필요한 기능을 모두 제공합니까?
[성능 효율성] 시스템의 응답 속도가 만족스럽습니까?"""

                question_generation_user_prompt = f"""1단계 분야 분석 결과:
{domain_analysis}

2단계 품질 속성 선정 결과:
{quality_selection}

소프트웨어 정보:
{input_text}

위 분석 결과를 바탕으로 ISO/IEC 25010 기반 설문조사 질문을 생성해주세요."""

                # 3단계 API 호출 - 질문 생성
                question_generation_response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": question_generation_prompt},
                        {"role": "user", "content": question_generation_user_prompt}
                    ],
                    temperature=0.7
                )
                
                initial_questions = question_generation_response.choices[0].message.content
                st.session_state.initial_questions = initial_questions
                st.session_state.step3_complete = True
                
                # 4단계: 질문 재조정
                progress_placeholder.info("🔧 4단계: 질문의 품질을 검증하고 재조정하고 있습니다...")
                
                # 4단계 시스템 프롬프트 - 질문 재조정
                refinement_prompt = """당신은 설문조사 설계 전문가입니다.
생성된 설문조사 질문들을 검토하고 다음 문제들을 찾아 수정하세요:

**검토 항목:**
1. **이중부정**: "~하지 않지 않습니까?" 같은 이중 부정 표현
   - 문제: 응답자 혼란 유발
   - 해결: 긍정문으로 변경

2. **모호한 척도**: "자주", "가끔", "빠른" 같은 주관적 표현
   - 문제: 응답자마다 다른 해석
   - 해결: 명확한 표현으로 변경 (구체적 기준을 제시하지는 말것)

3. **중복질문(유사질문)**: 여러 문항이 유사한 의미를 가지는 경우  
   - 문제: 중복 응답 유도 및 설문 피로도 증가  
   - 해결: 의미가 유사한 질문들은 **적절히 하나의 질문으로 통합** 

4. **유도질문**: 특정 답변을 유도하는 표현
   - 문제: 편향된 응답 유도
   - 해결: 중립적 표현으로 변경

**출력 형식:**
수정이 필요한 질문이 있는 경우:
문제 발견 및 수정 내역:
1. [문제 유형]: [원본 질문]
   → 문제점: [설명]
   → 수정: [수정된 질문]

수정이 필요없는 경우:
검토 완료: 모든 질문이 적절합니다. 수정 사항이 없습니다."""

                refinement_user_prompt = f"""다음 설문조사 질문들을 검토하고 필요시 수정해주세요:

{initial_questions}"""

                # 4단계 API 호출 - 질문 재조정
                refinement_response = client.chat.completions.create(
                    model=DEPLOYMENT_NAME,
                    messages=[
                        {"role": "system", "content": refinement_prompt},
                        {"role": "user", "content": refinement_user_prompt}
                    ],
                    temperature=0.3
                )
                
                refinement_result = refinement_response.choices[0].message.content
                st.session_state.refinement_result = refinement_result
                st.session_state.step4_complete = True
                
                # 최종 질문 생성 - 4단계에서 수정이 있었다면 반영
                if "수정 사항이 없습니다" in refinement_result or "모든 질문이 적절합니다" in refinement_result:
                    # 수정 사항이 없으면 3단계 질문 그대로 사용
                    final_questions = initial_questions
                else:
                    # 수정이 있었다면 3단계 질문에 수정 사항을 반영
                    # LLM을 한 번 더 호출하여 최종 질문 생성
                    final_generation_prompt = """당신은 설문조사 설계 전문가입니다.
3단계에서 생성된 초기 질문과 4단계의 수정 내역을 바탕으로 최종 설문조사 질문을 생성하세요.

**생성 규칙:**
1. 4단계에서 수정이 필요하다고 지적된 질문은 수정된 버전을 사용하세요.
2. 수정이 필요없었던 질문은 원본 그대로 사용하세요.
3. 모든 질문을 [품질 속성명] 질문 형식으로 출력하세요.
4. 질문만 나열하고 추가 설명은 붙이지 마세요."""

                    final_generation_user_prompt = f"""3단계 초기 질문:
{initial_questions}

4단계 수정 내역:
{refinement_result}

위 내용을 바탕으로 최종 설문조사 질문을 생성해주세요."""

                    final_generation_response = client.chat.completions.create(
                        model=DEPLOYMENT_NAME,
                        messages=[
                            {"role": "system", "content": final_generation_prompt},
                            {"role": "user", "content": final_generation_user_prompt}
                        ],
                        temperature=0.3
                    )
                    
                    final_questions = final_generation_response.choices[0].message.content
                
                st.session_state.final_questions = final_questions
                
                # 최종 질문을 품질속성과 질문으로 분리하여 저장 (요구사항 3)
                def parse_questions(questions_text):
                    """질문 텍스트를 파싱하여 품질속성과 질문을 분리"""
                    questions_data = []
                    pattern = r'\[([^\]]+)\]\s*(.+)'
                    
                    for line in questions_text.split('\n'):
                        line = line.strip()
                        if line and line.startswith('['):
                            match = re.match(pattern, line)
                            if match:
                                quality_attribute = match.group(1).strip()
                                question = match.group(2).strip()
                                questions_data.append({
                                    'quality_attribute': quality_attribute,
                                    'question': question,
                                    'display': f"[{quality_attribute}] {question}",
                                    'selected': True
                                })
                    
                    return questions_data
                
                questions_data = parse_questions(final_questions)
                
                # 세션 상태에 질문 저장 (새로 생성된 경우에만 초기화)
                current_questions_id = hash(final_questions)
                
                if 'questions_id' not in st.session_state or st.session_state.questions_id != current_questions_id:
                    st.session_state.questions_id = current_questions_id
                    st.session_state.questions_data = questions_data
                
                # 생성 완료 플래그 설정
                st.session_state.generation_complete = True
                progress_placeholder.success("✅ 모든 단계가 완료되었습니다!")
                
            except Exception as e:
                progress_placeholder.error(f"❌ 오류가 발생했습니다: {str(e)}")
                st.exception(e)

# 생성이 완료된 경우 결과 표시 (버튼 클릭과 무관하게) - 요구사항 2 반영
if st.session_state.get('generation_complete', False):
    st.markdown("---")
    st.markdown("### 📊 생성 결과")
    
    # 1단계 완료 메시지
    if st.session_state.get('step1_complete', False):
        st.success("✅ 1단계: 분야 분석 완료")
    
    # 2단계 완료 메시지
    if st.session_state.get('step2_complete', False):
        st.success("✅ 2단계: 품질 속성 선정 완료")
    
    # 3단계 완료 메시지
    if st.session_state.get('step3_complete', False):
        st.success("✅ 3단계: 초기 질문 생성 완료")
    
    # 4단계 완료 메시지
    if st.session_state.get('step4_complete', False):
        st.success("✅ 4단계: 질문 재조정 완료")
    
    st.markdown("---")
    
    # 1-4단계 결과 expander
    with st.expander("🔍 1단계: 분야 분석 결과 보기", expanded=False):
        st.markdown(st.session_state.domain_analysis)
    
    with st.expander("⚖️ 2단계: 품질 속성 선정 결과 보기", expanded=False):
        st.markdown(st.session_state.quality_selection)
    
    with st.expander("📝 3단계: 초기 질문 생성 결과 보기", expanded=False):
        st.markdown(st.session_state.initial_questions)
    
    with st.expander("🔧 4단계: 질문 재조정 결과 보기 (수정된 항목만 표시)", expanded=False):
        st.markdown(st.session_state.refinement_result)
    
    st.markdown("---")
    st.markdown("### ✏️ 질문 선택 및 수정")
    st.markdown("**원하는 질문을 선택하고, 필요시 질문 내용을 수정할 수 있습니다.**")
    
    # 질문 선택 및 수정 UI - 품질속성 고정, 질문만 수정 가능
    if 'questions_data' in st.session_state:
        for i, q_data in enumerate(st.session_state.questions_data):
            # 3컬럼 구조: 체크박스 | 품질속성(고정) | 질문(수정가능)
            with st.container():
                col1, col2, col3 = st.columns([0.5, 2.0, 7.5])
                
                with col1:
                    # 체크박스로 질문 선택
                    selected = st.checkbox(
                        "",
                        value=q_data.get('selected', True),
                        key=f"select_q_{i}_{st.session_state.questions_id}",
                        label_visibility="collapsed"
                    )
                    st.session_state.questions_data[i]['selected'] = selected
                
                with col2:
                    # 품질속성 표시 (고정, 읽기 전용) - 배지 스타일
                    quality_attr = q_data['quality_attribute']
                    st.markdown(
                        f"<div style='padding: 8px; background-color: #e3f2fd; border-radius: 5px; "
                        f"text-align: center; font-weight: bold; color: #1976d2; margin-top: 5px;'>"
                        f"{quality_attr}</div>",
                        unsafe_allow_html=True
                    )
                
                with col3:
                    # 질문만 수정 가능
                    edited_question = st.text_input(
                        f"질문 {i+1}",
                        value=q_data['question'],
                        key=f"edit_q_{i}_{st.session_state.questions_id}",
                        label_visibility="collapsed",
                        disabled=not selected
                    )
                    
                    if selected:
                        # 질문만 업데이트 (품질속성은 고정)
                        st.session_state.questions_data[i]['question'] = edited_question
                        st.session_state.questions_data[i]['display'] = f"[{quality_attr}] {edited_question}"
        
        st.markdown("---")
        
        # 선택된 질문만 표시
        selected_questions = [q for q in st.session_state.questions_data if q.get('selected', False)]
        
        if selected_questions:
            st.markdown("### 📊 선택된 최종 설문조사 질문")
            for idx, q_data in enumerate(selected_questions, 1):
                st.markdown(f"{idx}. {q_data['display']}")
        else:
            st.warning("⚠️ 선택된 질문이 없습니다.")
        
        # 최종 선택된 질문 텍스트
        selected_questions_text = "\n".join([f"{idx}. {q['display']}" for idx, q in enumerate(selected_questions, 1)])
        
        # 다운로드 및 저장 버튼
        full_result = f"""=== 1단계: 분야 분석 ===
{st.session_state.domain_analysis}

=== 2단계: 품질 속성 선정 ===
{st.session_state.quality_selection}

=== 3단계: 초기 질문 생성 ===
{st.session_state.initial_questions}

=== 4단계: 질문 재조정 ===
{st.session_state.refinement_result}

=== 선택된 최종 설문조사 질문 ===
{selected_questions_text}
"""
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            # 저장 및 다음단계 버튼
            if st.button("💾 저장 및 다음단계 (메트릭 구성)", type="primary", use_container_width=True):

                try:
                    with st.spinner("💾 설문 데이터를 저장 중입니다..."):
                        conn = get_connection()
                        cur = conn.cursor()

                        # 1️⃣ surveys 테이블에 기본 정보 저장
                        cur.execute("""
                            INSERT INTO surveys (
                                project_name, software_description, evaluation_purpose,
                                respondent_info, expected_respondents, development_scale,
                                user_scale, operating_environment, industry_field, survey_item_count
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            RETURNING id;
                        """, (
                            st.session_state.project_name,
                            st.session_state.software_description,
                            st.session_state.evaluation_purpose,
                            st.session_state.respondent_info,
                            st.session_state.expected_respondents,
                            st.session_state.development_scale,
                            st.session_state.user_scale,
                            st.session_state.operating_environment,
                            st.session_state.industry_field,
                            st.session_state.survey_item_count
                        ))

                        survey_id = cur.fetchone()[0]

                        # 2️⃣ generation_steps 테이블에 1~4단계 결과 저장
                        steps_data = [
                            (survey_id, 1, "도메인 분석", st.session_state.domain_analysis),
                            (survey_id, 2, "품질 속성 선정", st.session_state.quality_selection),
                            (survey_id, 3, "초기 질문 생성", st.session_state.initial_questions),
                            (survey_id, 4, "질문 재조정", st.session_state.refinement_result)
                        ]

                        execute_values(cur, """
                            INSERT INTO generation_steps (
                                survey_id, step_number, step_name, step_result
                            ) VALUES %s;
                        """, steps_data)

                        # 3️⃣ survey_questions 테이블에 선택된 질문만 저장 (is_selected 제거)
                        # 선택된 질문만 필터링하고, question_order는 화면 표시 순서대로 저장
                        selected_questions_for_db = [
                            (
                                survey_id,
                                idx + 1,  # question_order는 화면에 나온 순서대로
                                q["quality_attribute"],
                                q["question"]
                            )
                            for idx, q in enumerate(selected_questions)
                        ]

                        if selected_questions_for_db:
                            execute_values(cur, """
                                INSERT INTO survey_questions (
                                    survey_id, question_order, quality_attribute, question_text
                                ) VALUES %s;
                            """, selected_questions_for_db)

                        # 커밋 및 종료
                        conn.commit()
                        cur.close()
                        conn.close()

                        st.success(f"✅ 설문 데이터가 성공적으로 저장되었습니다!")
                        st.info("👉 다음 단계인 [메트릭 구성]으로 이동할 수 있습니다.")
                        st.session_state.selected_survey_id = survey_id

                        st.cache_data.clear()

                except Exception as e:
                    st.error(f"❌ DB 저장 중 오류 발생: {e}")
                    st.exception(e)
        
        with col_btn2:
            # 전체 결과 다운로드 버튼
            st.download_button(
                label="📥 전체 결과 다운로드 (TXT)",
                data=full_result,
                file_name="survey_full_report.txt",
                mime="text/plain",
                use_container_width=True
            )

# 하단 정보
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    ISO/IEC 25010 기반 SW 품질 평가 설문조사 생성기<br>
    Powered by Azure OpenAI & Streamlit
</div>
""", unsafe_allow_html=True)