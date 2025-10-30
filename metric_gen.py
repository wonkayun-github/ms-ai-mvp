import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI
import psycopg2

load_dotenv()

# 환경 변수 로드
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

# Streamlit 페이지 설정
st.set_page_config(
    page_title="SW 평가 설문조사 메트릭 구성",
    page_icon="📊",
    layout="wide"
)

# --- 세션 상태 초기화 ---
if "project_searched" not in st.session_state:
    st.session_state.project_searched = False
if "last_project_name" not in st.session_state:
    st.session_state.last_project_name = None
if "all_metrics" not in st.session_state:
    st.session_state.all_metrics = []
if "metrics_generated" not in st.session_state:
    st.session_state.metrics_generated = False

# 제목
st.title("📊 메트릭 구성")
st.markdown("**ISO/IEC 25010 품질 속성 기반 평가 메트릭 설계**")
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

# 프로젝트 목록 조회 함수
@st.cache_data(ttl=None)
def get_project_list():
    """저장된 모든 프로젝트 조회"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, project_name, software_description, created_at 
            FROM surveys 
            ORDER BY created_at DESC
        """)
        projects = cur.fetchall()
        cur.close()
        conn.close()
        return projects
    except Exception as e:
        st.error(f"❌ 프로젝트 조회 중 오류 발생: {e}")
        return []


# 프로젝트의 질문 조회 함수
@st.cache_data(ttl=None)
def get_questions_by_project(survey_id):
    """특정 프로젝트의 질문 조회"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, question_order, quality_attribute, question_text 
            FROM survey_questions 
            WHERE survey_id = %s 
            ORDER BY question_order ASC
        """, (survey_id,))
        questions = cur.fetchall()
        cur.close()
        conn.close()
        return questions
    except Exception as e:
        st.error(f"❌ 질문 조회 중 오류 발생: {e}")
        return []


# ==================== 메인 UI ====================

st.markdown("### 📋 1단계: 프로젝트 선택")

projects = get_project_list()

if not projects:
    st.info("ℹ️ 저장된 프로젝트가 없습니다. 먼저 설문을 생성해주세요.")
else:
    col1, col2 = st.columns([8, 2])
    with col1:
        project_options = [f"{p[1]}" for p in projects]
        selected_project_name = st.selectbox(
            "프로젝트 선택 *",
            project_options,
            help="메트릭을 구성할 프로젝트를 선택하세요.",
            key="selected_project"
        )
    with col2:
        st.markdown("<div style='height: 26px'></div>", unsafe_allow_html=True)
        search_button = st.button("🔍 조회", use_container_width=True, key="search_button")

    if "project_searched" not in st.session_state:
        st.session_state.project_searched = False

    if search_button:
        st.session_state.project_searched = True
    elif selected_project_name != st.session_state.get("last_project_name"):
        st.session_state.project_searched = False

    st.session_state.last_project_name = selected_project_name

    selected_project = next((p for p in projects if p[1] == selected_project_name), None)

    if selected_project and st.session_state.project_searched:
        selected_survey_id = selected_project[0]

        with st.expander("📌 선택된 프로젝트 정보", expanded=True):
            st.markdown(f"**프로젝트명:** {selected_project[1]}")
            st.markdown(f"**소프트웨어 설명:** {selected_project[2]}")
            st.markdown(f"**생성 일시:** {selected_project[3]}")

        st.divider()
        
        # 질문 조회
        questions = get_questions_by_project(selected_survey_id)
        
        if questions:
            st.markdown("### 📝 생성된 설문조사 질문")
            st.markdown(f"**총 {len(questions)}개 질문**")
            with st.expander("질문 목록 보기", expanded=True):
                for q in questions:
                    st.markdown(f"**{q[1]}.** [{q[2]}] {q[3]}")
            
            st.divider()
            
            # 척도 선택
            st.markdown("### ⚖️ 2단계: 척도 선택")
            scale_options = {
                "리커트 척도 (5단계)": "likert_5",
                "숫자 평정 척도 (1~100점)": "numeric_100"
            }
            selected_scale_name = st.radio(
                "평가 척도 선택 *",
                options=list(scale_options.keys()),
                help="설문조사에서 사용할 평가 척도를 선택하세요.",
                key="scale_selection"
            )
            selected_scale_type = scale_options[selected_scale_name]
            
            # 척도 설명
            if selected_scale_type == "likert_5":
                st.info("📌 **리커트 척도 (5단계)**\n"
                        "- 매우 그렇지 않다\n"
                        "- 그렇지 않다\n"
                        "- 보통이다\n"
                        "- 그렇다\n"
                        "- 매우 그렇다")
            else:
                st.info("📌 **숫자 평정 척도 (1~100점)**\n"
                        "- 응답자가 1점~100점 사이의 값으로 평가\n"
                        "- 더 세분화된 평가 가능")
            
            st.divider()

            # 메트릭 생성 버튼
            if st.button("🚀 메트릭 생성하기", type="primary", use_container_width=True):
                progress_placeholder = st.empty()
                status_container = st.container()
                
                try:
                    client = AzureOpenAI(
                        azure_endpoint=AZURE_OPENAI_ENDPOINT,
                        api_key=AZURE_OPENAI_API_KEY,
                        api_version="2024-02-15-preview"
                    )
                    
                    progress_placeholder.info("🔄 질문별 메트릭 생성 시작...")
                    
                    # 척도 설명
                    if selected_scale_type == "likert_5":
                        scale_description = """리커트 척도 (5단계):
매우 그렇다
그렇다
보통이다
그렇지 않다
매우 그렇지 않다"""
                    else:
                        scale_description = """숫자 평정 척개 (1~100점):
100~81점: 매우 긍정적
80~61점 : 긍정적
60~41점 : 중립
40~21점 : 부정적
20~1점  : 매우 부정적"""

                    # 예시 JSON
                    if selected_scale_type == "likert_5":
                        example_json = """
출력 형식(JSON 배열, 1개 항목):
{
  "question_order": 1,
  "quality_attribute": "기능적 적합성",
  "question_text": "시스템은 요구된 기능을 정확하게 수행하는가?",
  "scale_interpretations": [
    { "scale_order": 5, "scale": "매우 그렇다", "description": "모든 기능이 완벽하게 수행된다." },
    { "scale_order": 4, "scale": "그렇다", "description": "대부분의 기능이 정확하게 수행된다." },
    { "scale_order": 3, "scale": "보통이다", "description": "대부분 수행되지만 일부 오류가 있다." },
    { "scale_order": 2, "scale": "그렇지 않다", "description": "일부 기능이 작동하지 않는다." },
    { "scale_order": 1, "scale": "매우 그렇지 않다", "description": "요구된 기능을 거의 수행하지 못한다." }
  ]
}
"""
                    else:
                        example_json = """
출력 형식(JSON 배열, 1개 항목):
{
  "question_order": 1,
  "quality_attribute": "기능적 적합성",
  "question_text": "시스템은 요구된 기능을 정확하게 수행하는가?",
  "scale_interpretations": [
    { "scale_order": 5, "scale": "100~81점", "description": "모든 기능이 완벽하게 수행된다." },
    { "scale_order": 4, "scale": "80~61점", "description": "대부분의 기능이 정확하게 수행된다." },
    { "scale_order": 3, "scale": "60~41점", "description": "일부 오류가 있으나 대부분 수행된다." },
    { "scale_order": 2, "scale": "40~21점", "description": "주요 기능 중 일부가 작동하지 않는다." },
    { "scale_order": 1, "scale": "20~1점", "description": "요구된 기능을 거의 수행하지 못한다." }
  ]
}
"""

                    # 질문별로 메트릭 생성 (병렬 처리)
                    # session_state에 저장 (리렌더링 후에도 유지)
                    st.session_state.all_metrics = []
                    
                    for idx, q in enumerate(questions, 1):
                        question_order = q[1]
                        quality_attr = q[2]
                        question_text = q[3]
                        
                        # 진행 상황 업데이트
                        progress_placeholder.info(
                            f"🔄 진행 중... ({idx}/{len(questions)}) Q{question_order}. {question_text[:40]}..."
                        )
                        
                        # 각 질문별 프롬프트 생성
                        single_metric_prompt = f"""
당신은 ISO/IEC 25010 기반의 소프트웨어 품질 평가 전문가입니다.
다음 질문에 대해, 평가척도별로 평가자가 참고할 수 있는 '구간별 설명'을 생성하세요.

**평가 척도**
{scale_description}

**질문**
Q{question_order}. [{quality_attr}] {question_text}

⚠️ 생성 규칙:
- 항상 높은 점수(긍정적 평가)에서 낮은 점수(부정적 평가) 순으로 생성하세요.
- 각 scale_interpretations 항목은 반드시 아래 3개의 키를 모두 포함해야 합니다.
  1. "scale_order" (정수)
  2. "scale" (척도명)
  3. "description" (문장형 설명)
- 어떤 경우에도 "description"은 생략하지 마세요.
- JSON 객체 1개만 생성하세요 (배열 아님).

{example_json}
"""
                        
                        # LLM 호출 (각 질문별)
                        response = client.chat.completions.create(
                            model=DEPLOYMENT_NAME,
                            messages=[
                                {"role": "system", "content": "당신은 소프트웨어 품질 평가 전문가입니다. JSON만 반환하세요."},
                                {"role": "user", "content": single_metric_prompt}
                            ],
                            temperature=0.3
                        )
                        
                        content = response.choices[0].message.content.strip()
                        
                        # JSON 파싱
                        try:
                            metric_obj = json.loads(content)
                            st.session_state.all_metrics.append(metric_obj)
                        except json.JSONDecodeError:
                            st.error(f"❌ Q{question_order} JSON 파싱 실패")
                            st.text(content)
                            st.stop()
                    
                    progress_placeholder.success(f"✅ 모든 질문의 메트릭 생성 완료!")
                    st.session_state.metrics_generated = True

                except Exception as e:
                    progress_placeholder.error(f"❌ 오류 발생: {str(e)}")
                    with st.expander("📋 오류 상세 정보", expanded=True):
                        st.exception(e)
            
            # 메트릭이 생성되었으면 표시 (버튼 밖에서도 유지)
            if st.session_state.metrics_generated and len(st.session_state.all_metrics) > 0:
                st.divider()
                st.markdown("### 📊 생성된 메트릭 확인")
                for metric_info in st.session_state.all_metrics:
                    question_order = metric_info["question_order"]
                    qa = metric_info["quality_attribute"]
                    qtext = metric_info["question_text"]
                    with st.expander(f"**{question_order}**. [{qa}] {qtext}", expanded=False):
                        for scale_obj in sorted(metric_info["scale_interpretations"], key=lambda x: x["scale_order"], reverse=True):
                            desc = scale_obj.get("description", "(설명이 없습니다)")
                            st.markdown(f"**{scale_obj['scale']}** : {desc}")

                st.divider()

                # 메트릭 저장 버튼 (버튼 밖에서)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 메트릭 저장하기", type="primary", use_container_width=True, key="save_metrics_outside"):
                        save_status = st.empty()
                        try:
                            conn = get_connection()
                            cur = conn.cursor()
                            
                            # metrics 테이블에 저장
                            for idx, metric_info in enumerate(st.session_state.all_metrics, 1):
                                question_order = metric_info["question_order"]
                                
                                # 해당 question_order를 가진 question_id 찾기
                                question_id = None
                                for q in questions:
                                    if q[1] == question_order:
                                        question_id = q[0]
                                        break
                                
                                if question_id:
                                    # scale_interpretations를 JSON 문자열로 변환
                                    element_description = json.dumps(
                                        metric_info["scale_interpretations"],
                                        ensure_ascii=False
                                    )
                                    
                                    cur.execute("""
                                        INSERT INTO metrics 
                                        (survey_id, question_id, scale_type, element_description)
                                        VALUES (%s, %s, %s, %s)
                                    """, (selected_survey_id, question_id, selected_scale_type, element_description))
                                    
                                    save_status.info(f"💾 저장 중... ({idx}/{len(st.session_state.all_metrics)})")
                            
                            conn.commit()
                            cur.close()
                            conn.close()
                            
                            save_status.empty()
                            st.success("✅ 메트릭이 성공적으로 저장되었습니다!")
                            st.info("👉 다음: 평가 프레임워크 생성으로 이동할 수 있습니다.")
                        except Exception as save_error:
                            st.error(f"❌ 메트릭 저장 중 오류 발생: {str(save_error)}")
                            st.exception(save_error)
                
                with col2:
                    # 메트릭 JSON 다운로드
                    metrics_json = json.dumps(st.session_state.all_metrics, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="📥 메트릭 데이터 다운로드 (JSON)",
                        data=metrics_json,
                        file_name=f"metrics_{selected_project_name}.json",
                        mime="application/json",
                        use_container_width=True,
                        key="download_metrics_outside"
                    )

                st.divider()
        else:
            st.warning("⚠️ 선택된 프로젝트에 질문이 없습니다.")

# 하단 정보
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    ISO/IEC 25010 기반 SW 품질 평가 메트릭 구성<br>
    Powered by Azure OpenAI & Streamlit
</div>
""", unsafe_allow_html=True)
