import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="SW 평가 설문조사 시스템",
    page_icon="📋",
    layout="wide"
)

# 멀티페이지 네비게이션 설정
pages = [
    st.Page("survey_gen.py", title="1단계: 질문 생성", icon="📝"),
    st.Page("metric_gen.py", title="2단계: 메트릭 구성", icon="📊"),
    # st.Page("framework_gen.py", title="3단계: 평가 프레임워크 생성", icon="🎯"),
    st.Page("iso25010_rag.py", title="RAG 데이터 구성", icon="⚙️"),
]

page = st.navigation(pages)

# ✅ 세션 상태 기반 초기 페이지 강제 지정
if "navigated" not in st.session_state:
    st.session_state.navigated = True
    st.switch_page("survey_gen.py")   # 🎯 여기서 디폴트 페이지 지정

# 페이지 실행
page.run()
