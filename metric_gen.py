import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed

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
st.title("📋 품질기반 SW 설문조사 설계 에이전트")
st.markdown("**SW 제품의 품질모델을 정의하는 국제표준인 ISO/IEC 25010 기반으로 설문조사를 설계하여, SW 제품의 품질평가에 도움을 주기위한 목적의 에이전트 입니다.**")
st.divider()


# DB 연결 함수 (에러 처리 강화)
def get_connection():
    """PostgreSQL 연결"""
    try:
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
    except psycopg2.OperationalError as e:
        st.error(f"❌ 데이터베이스 연결 실패: 네트워크 또는 DB 서버를 확인해주세요.")
        st.error(f"상세 오류: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ 예상치 못한 DB 연결 오류가 발생했습니다.")
        st.error(f"상세 오류: {str(e)}")
        return None

# 프로젝트 목록 조회 함수
@st.cache_data(ttl=None)
def get_project_list():
    """저장된 모든 프로젝트 조회"""
    try:
        conn = get_connection()
        if conn is None:
            return []
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
        if conn is None:
            return []
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


# LLM 응답 검증 함수
def validate_metric_response(metric_obj, question_order):
    """LLM 응답의 필수 키 검증"""
    required_keys = ["question_order", "quality_attribute", "question_text", "scale_interpretations"]
    missing_keys = [key for key in required_keys if key not in metric_obj]
    
    if missing_keys:
        st.warning(f"⚠️ Q{question_order}: 필수 키 누락 ({', '.join(missing_keys)})")
        return False
    
    # scale_interpretations 내부 검증
    if not isinstance(metric_obj["scale_interpretations"], list):
        st.warning(f"⚠️ Q{question_order}: scale_interpretations가 배열이 아닙니다.")
        return False
    
    for idx, scale_obj in enumerate(metric_obj["scale_interpretations"]):
        required_scale_keys = ["scale_order", "scale", "description"]
        missing_scale_keys = [key for key in required_scale_keys if key not in scale_obj]
        if missing_scale_keys:
            st.warning(f"⚠️ Q{question_order} 척도 {idx+1}: 필수 키 누락 ({', '.join(missing_scale_keys)})")
            return False
    
    return True


# 단일 질문 메트릭 생성 함수 (병렬 처리용)
def generate_single_metric(client, question_data, scale_description, example_json, selected_scale_type):
    """단일 질문에 대한 메트릭 생성"""
    question_id, question_order, quality_attr, question_text = question_data
    
    try:
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
            
            # 응답 검증
            if validate_metric_response(metric_obj, question_order):
                return {
                    "success": True,
                    "question_order": question_order,
                    "metric": metric_obj
                }
            else:
                return {
                    "success": False,
                    "question_order": question_order,
                    "error": "응답 검증 실패"
                }
        except json.JSONDecodeError as je:
            return {
                "success": False,
                "question_order": question_order,
                "error": f"JSON 파싱 실패: {str(je)}"
            }
    
    except Exception as e:
        return {
            "success": False,
            "question_order": question_order,
            "error": f"API 호출 실패: {str(e)}"
        }


# ==================== 메인 UI ====================

st.markdown("## 📊 2단계: 메트릭 구성")

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

    # 세션 상태 관리 개선 (요구사항 3-1)
    if search_button:
        st.session_state.project_searched = True
        # 새로 조회 시작 시 이전 메트릭 데이터 초기화
        st.session_state.all_metrics = []
        st.session_state.metrics_generated = False
    elif selected_project_name != st.session_state.get("last_project_name"):
        # 프로젝트 변경 시 초기화
        st.session_state.project_searched = False
        st.session_state.all_metrics = []
        st.session_state.metrics_generated = False

    st.session_state.last_project_name = selected_project_name

    selected_project = next((p for p in projects if p[1] == selected_project_name), None)

    if selected_project and st.session_state.project_searched:
        selected_survey_id = selected_project[0]

        with st.expander("📌 선택된 프로젝트 정보", expanded=True):
            st.markdown(f"**프로젝트명:** {selected_project[1]}")
            st.markdown(f"**소프트웨어 설명:** {selected_project[2]}")

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
            st.markdown("### ⚖️ 평가 척도")
            
            # 기존 메트릭 존재 여부 확인
            try:
                conn = get_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT m.scale_type, m.question_id, m.element_description, sq.question_order, sq.quality_attribute, sq.question_text
                        FROM metrics m
                        JOIN survey_questions sq ON m.question_id = sq.id
                        WHERE m.survey_id = %s
                        ORDER BY sq.question_order ASC
                    """, (selected_survey_id,))
                    existing_metrics = cur.fetchall()
                    cur.close()
                    conn.close()
                else:
                    existing_metrics = []
            except Exception as e:
                st.error(f"❌ 메트릭 조회 중 오류: {str(e)}")
                existing_metrics = []
            
            # 기존 메트릭이 있는 경우
            if existing_metrics:
                # 척도 타입 확인 (첫 번째 레코드에서)
                scale_type = existing_metrics[0][0]
                scale_name_display = "리커트 척도 (5단계)" if scale_type == "likert_5" else "숫자 평정 척도 (1~100점)"
                
                st.info(f"📌 **사용된 평가 척도:** {scale_name_display}")
                st.success(f"✅ 이 프로젝트의 메트릭이 이미 구성되어 있습니다. (총 {len(existing_metrics)}개)")
                
                # 기존 메트릭 표시
                st.markdown("### 📊 구성된 메트릭")
                for metric_row in existing_metrics:
                    scale_type_db, question_id, element_description_json, question_order, quality_attr, question_text = metric_row
                    
                    # JSON 파싱
                    try:
                        scale_interpretations = json.loads(element_description_json)
                        with st.expander(f"**{question_order}**. [{quality_attr}] {question_text}", expanded=False):
                            for scale_obj in sorted(scale_interpretations, key=lambda x: x.get("scale_order", 0), reverse=True):
                                desc = scale_obj.get("description", "(설명이 없습니다)")
                                st.markdown(f"**{scale_obj.get('scale', 'N/A')}** : {desc}")
                    except json.JSONDecodeError:
                        st.error(f"Q{question_order}: JSON 파싱 오류")
                
                st.divider()
                
                # 메트릭 재생성 옵션
                st.markdown("### 🔄 메트릭 재구성")
                st.warning("⚠️ 메트릭을 재생성하면 기존 메트릭이 삭제됩니다.")
                
                col_recreate1, col_recreate2 = st.columns([1, 1])
                
                with col_recreate1:
                    if st.button("🔄 메트릭 재생성하기", use_container_width=True):
                        # 기존 메트릭 삭제
                        try:
                            conn = get_connection()
                            if conn:
                                cur = conn.cursor()
                                cur.execute("DELETE FROM metrics WHERE survey_id = %s", (selected_survey_id,))
                                conn.commit()
                                
                                # surveys 테이블의 metric_completed 플래그를 N으로 업데이트
                                cur.execute("""
                                    UPDATE surveys 
                                    SET metric_completed = 'N', updated_at = CURRENT_TIMESTAMP
                                    WHERE id = %s
                                """, (selected_survey_id,))
                                conn.commit()
                                
                                cur.close()
                                conn.close()
                                st.success("✅ 기존 메트릭이 삭제되었습니다. 페이지를 새로고침하여 새로 생성하세요.")
                                st.rerun()
                        except Exception as del_error:
                            st.error(f"❌ 삭제 중 오류: {str(del_error)}")
                
                # 요구사항 2: 설문 생성결과 다운로드 버튼 강조
                st.divider()
                st.markdown("### 📄 최종 결과물")
                
                # 요구사항 1: 명시적 메트릭 존재 체크
                if len(existing_metrics) > 0:
                    # Markdown 형식으로 내용 생성
                    pdf_content = f"""# 설문조사 메트릭 생성 결과

## 프로젝트 정보
- **프로젝트명:** {selected_project[1]}
- **소프트웨어 설명:** {selected_project[2]}

---

## 질문 및 메트릭

"""
                    for metric_row in existing_metrics:
                        scale_type_db, question_id, element_description_json, question_order, quality_attr, question_text = metric_row
                        
                        pdf_content += f"### {question_order}. [{quality_attr}] {question_text}\n\n"
                        pdf_content += "**평가 척도**\n\n"
                        
                        try:
                            scale_interpretations = json.loads(element_description_json)
                            for scale_obj in sorted(scale_interpretations, key=lambda x: x.get("scale_order", 0), reverse=True):
                                scale_name = scale_obj.get('scale', 'N/A')
                                desc = scale_obj.get("description", "(설명이 없습니다)")
                                pdf_content += f"- **{scale_name}**: {desc}\n"
                        except:
                            pdf_content += "- (메트릭 정보 파싱 오류)\n"
                        
                        pdf_content += "\n---\n\n"
                    
                    # 강조된 다운로드 버튼
                    st.download_button(
                        label="📄 설문 생성결과 다운로드 (md)",
                        data=pdf_content,
                        file_name=f"survey_result_{selected_project_name}.md",
                        mime="text/markdown",
                        type="primary",
                        use_container_width=True,
                        key="download_survey_pdf"
                    )
                    st.success("✅ 최종 설문 결과가 준비되었습니다. 위 버튼을 클릭하여 다운로드하세요.")
                else:
                    # 메트릭이 없는 경우 (명시적 체크)
                    st.error("❌ 다운로드할 메트릭 데이터가 없습니다.")
                    st.info("메트릭을 먼저 생성해주세요.")
            
            # 기존 메트릭이 없는 경우 - 기존 로직
            else:
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

                # 메트릭 생성 버튼 (기존 메트릭이 없을 때만)
                if not existing_metrics:
                    if st.button("🚀 메트릭 생성하기", type="primary", use_container_width=True):
                        # 메트릭 생성 시작 시 이전 데이터 클리어 (요구사항 3-3)
                        st.session_state.all_metrics = []
                        st.session_state.metrics_generated = False
                        
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

                            # 병렬 처리로 메트릭 생성 (요구사항 1)
                            total_questions = len(questions)
                            completed_count = 0
                            failed_questions = []
                            
                            # ThreadPoolExecutor로 병렬 처리 (max_workers=5)
                            with ThreadPoolExecutor(max_workers=5) as executor:
                                # 모든 질문에 대한 Future 객체 생성
                                future_to_question = {
                                    executor.submit(
                                        generate_single_metric,
                                        client,
                                        q,
                                        scale_description,
                                        example_json,
                                        selected_scale_type
                                    ): q for q in questions
                                }
                                
                                # 완료되는 대로 처리
                                for future in as_completed(future_to_question):
                                    result = future.result()
                                    completed_count += 1
                                    
                                    # 진행 상황 표시 (요구사항 1)
                                    progress_placeholder.info(f"🔄 진행 중... 완료: {completed_count}/{total_questions}")
                                    
                                    if result["success"]:
                                        st.session_state.all_metrics.append(result["metric"])
                                    else:
                                        # API 에러 발생 시 해당 질문만 스킵 (요구사항 1, 2-1)
                                        failed_questions.append({
                                            "question_order": result["question_order"],
                                            "error": result["error"]
                                        })
                                        st.warning(f"⚠️ Q{result['question_order']} 생성 실패: {result['error']}")
                            
                            # 정렬 (question_order 기준)
                            st.session_state.all_metrics.sort(key=lambda x: x["question_order"])
                            
                            # 완료 메시지
                            if len(st.session_state.all_metrics) == total_questions:
                                progress_placeholder.success(f"✅ 모든 질문의 메트릭 생성 완료!")
                            else:
                                progress_placeholder.warning(
                                    f"⚠️ 메트릭 생성 완료: {len(st.session_state.all_metrics)}/{total_questions}개 성공, "
                                    f"{len(failed_questions)}개 실패"
                                )
                            
                            # 실패한 질문 상세 정보
                            if failed_questions:
                                with st.expander("❌ 실패한 질문 상세 정보", expanded=False):
                                    for failed in failed_questions:
                                        st.error(f"Q{failed['question_order']}: {failed['error']}")
                            
                            st.session_state.metrics_generated = True

                        except Exception as e:
                            progress_placeholder.error(f"❌ 전체 프로세스 오류 발생: {str(e)}")
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
                col1, col2 = st.columns([1, 1])
                
                # 세션 상태 초기화
                if "show_save_confirmation" not in st.session_state:
                    st.session_state.show_save_confirmation = False
                if "save_action_choice" not in st.session_state:
                    st.session_state.save_action_choice = None
                
                with col1:
                    # 저장 버튼 클릭
                    if st.button("💾 메트릭 저장하기", type="primary", use_container_width=True, key="save_metrics_outside"):
                        try:
                            conn = get_connection()
                            if conn is None:
                                st.error("❌ DB 연결 실패로 저장할 수 없습니다.")
                            else:
                                cur = conn.cursor()
                                
                                # 중복 체크: 기존 메트릭 존재 여부 확인
                                cur.execute("""
                                    SELECT COUNT(*) FROM metrics 
                                    WHERE survey_id = %s
                                """, (selected_survey_id,))
                                exists_count = cur.fetchone()[0]
                                
                                cur.close()
                                conn.close()
                                
                                # 기존 메트릭이 존재하는 경우
                                if exists_count > 0:
                                    st.session_state.show_save_confirmation = True
                                    st.session_state.existing_metrics_count = exists_count
                                else:
                                    # 기존 메트릭 없으면 바로 저장
                                    st.session_state.save_action_choice = "direct_save"
                                    st.rerun()
                                    
                        except Exception as check_error:
                            st.error(f"❌ 메트릭 확인 중 오류 발생: {str(check_error)}")
                
                # 요구사항 2: 설문 생성결과 다운로드 버튼 강조 (별도 섹션)
                st.divider()
                st.markdown("### 📄 최종 결과물")
                
                # 요구사항 1: 명시적 메트릭 존재 체크
                if len(st.session_state.all_metrics) > 0:
                    # Markdown 형식으로 내용 생성
                    pdf_content = f"""# 설문조사 메트릭 생성 결과

## 프로젝트 정보
- **프로젝트명:** {selected_project_name}
- **소프트웨어 설명:** {selected_project[2]}

---

## 질문 및 메트릭

"""
                    for metric_info in st.session_state.all_metrics:
                        question_order = metric_info["question_order"]
                        quality_attr = metric_info["quality_attribute"]
                        question_text = metric_info["question_text"]
                        
                        pdf_content += f"### {question_order}. [{quality_attr}] {question_text}\n\n"
                        pdf_content += "**평가 척도**\n\n"
                        
                        for scale_obj in sorted(metric_info["scale_interpretations"], key=lambda x: x.get("scale_order", 0), reverse=True):
                            scale_name = scale_obj.get('scale', 'N/A')
                            desc = scale_obj.get("description", "(설명이 없습니다)")
                            pdf_content += f"- **{scale_name}**: {desc}\n"
                        
                        pdf_content += "\n---\n\n"
                    
                    # 강조된 다운로드 버튼
                    st.download_button(
                        label="📄 설문 생성결과 다운로드 (PDF)",
                        data=pdf_content,
                        file_name=f"survey_result_{selected_project_name}.md",
                        mime="text/markdown",
                        type="primary",
                        use_container_width=True,
                        key="download_metrics_outside"
                    )
                    st.success("✅ 최종 설문 결과가 준비되었습니다. 위 버튼을 클릭하여 다운로드하세요.")
                else:
                    # 메트릭이 없는 경우 (명시적 체크)
                    st.error("❌ 다운로드할 메트릭 데이터가 없습니다.")
                    st.info("메트릭을 먼저 생성해주세요.")
                
                # 중복 확인 UI 표시 (컬럼 밖)
                if st.session_state.show_save_confirmation:
                    st.warning(f"⚠️ 이 프로젝트의 메트릭이 이미 {st.session_state.existing_metrics_count}개 존재합니다.")
                    
                    # 사용자 선택지 제공
                    st.markdown("##### 처리 방법을 선택하세요:")
                    action = st.radio(
                        "선택",
                        ["❌ 취소 (저장하지 않음)", 
                         "🔄 기존 메트릭 삭제 후 새로 저장"],
                        key="save_action_radio",
                        label_visibility="collapsed"
                    )
                    
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button("✅ 확인", type="primary", use_container_width=True, key="confirm_save_action"):
                            if action == "❌ 취소 (저장하지 않음)":
                                st.session_state.show_save_confirmation = False
                                st.session_state.save_action_choice = None
                                st.info("ℹ️ 저장이 취소되었습니다.")
                                st.rerun()
                            elif action == "🔄 기존 메트릭 삭제 후 새로 저장":
                                st.session_state.save_action_choice = "delete_and_save"
                                st.session_state.show_save_confirmation = False
                                st.rerun()
                    
                    with col_cancel:
                        if st.button("🚫 취소", use_container_width=True, key="cancel_save_action"):
                            st.session_state.show_save_confirmation = False
                            st.session_state.save_action_choice = None
                            st.info("ℹ️ 저장이 취소되었습니다.")
                            st.rerun()
                
                # 실제 저장 실행 (컬럼 밖으로 이동)
                if st.session_state.save_action_choice in ["direct_save", "delete_and_save"]:
                    save_status = st.empty()
                    try:
                        conn = get_connection()
                        if conn is None:
                            st.error("❌ DB 연결 실패로 저장할 수 없습니다.")
                            st.session_state.save_action_choice = None
                        else:
                            cur = conn.cursor()
                            
                            # 기존 메트릭 삭제 (선택한 경우)
                            if st.session_state.save_action_choice == "delete_and_save":
                                save_status.info(f"🗑️ 기존 메트릭 삭제 중... (survey_id: {selected_survey_id})")
                                
                                # 삭제 전 카운트 확인
                                cur.execute("SELECT COUNT(*) FROM metrics WHERE survey_id = %s", (selected_survey_id,))
                                before_count = cur.fetchone()[0]
                                st.info(f"🔍 삭제 전 메트릭 개수: {before_count}")
                                
                                # 삭제 실행
                                cur.execute("""
                                    DELETE FROM metrics 
                                    WHERE survey_id = %s
                                """, (selected_survey_id,))
                                deleted_rows = cur.rowcount
                                st.info(f"🔍 DELETE 영향받은 행: {deleted_rows}")
                                
                                conn.commit()
                                
                                # 삭제 후 카운트 확인
                                cur.execute("SELECT COUNT(*) FROM metrics WHERE survey_id = %s", (selected_survey_id,))
                                after_count = cur.fetchone()[0]
                                st.info(f"🔍 삭제 후 메트릭 개수: {after_count}")
                                
                                save_status.success(f"✅ 기존 메트릭 {deleted_rows}개 삭제 완료")
                            
                            # metrics 테이블에 저장
                            save_status.info("💾 메트릭 저장 시작...")
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
                            
                            # surveys 테이블의 metric_completed 플래그를 Y로 업데이트
                            cur.execute("""
                                UPDATE surveys 
                                SET metric_completed = 'Y', updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (selected_survey_id,))
                            conn.commit()
                            
                            cur.close()
                            conn.close()
                            
                            save_status.empty()
                            st.success("✅ 메트릭이 성공적으로 저장되었습니다!")
                            st.info("👉 다음: 평가 프레임워크 생성으로 이동할 수 있습니다.")
                            
                            # 메트릭 저장 완료 시 상태 정리 (요구사항 3-2)
                            st.session_state.all_metrics = []
                            st.session_state.metrics_generated = False
                            st.session_state.save_action_choice = None
                            st.session_state.show_save_confirmation = False
                            
                    except Exception as save_error:
                        st.error(f"❌ 메트릭 저장 중 오류 발생: {str(save_error)}")
                        st.exception(save_error)
                        st.session_state.save_action_choice = None
                        st.session_state.show_save_confirmation = False

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
