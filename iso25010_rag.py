import streamlit as st
import os, uuid, time
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchableField,
    SimpleField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# === 환경 변수 로드 ===
load_dotenv()

# === Azure 환경변수 ===
# OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME", "gpt-4.1-mini")
DEPLOYMENT_EMBEDDING_NAME = os.getenv("DEPLOYMENT_EMBEDDING_NAME", "text-embedding-3-small")

# AI Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "iso25010-index")

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "docs")

# === 클라이언트 설정 ===
blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=AZURE_STORAGE_ACCOUNT_KEY
)

search_endpoint = AZURE_SEARCH_ENDPOINT
search_key = AZURE_SEARCH_API_KEY
index_name = AZURE_SEARCH_INDEX_NAME

openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=OPENAI_API_VERSION
)

# === Blob 컨테이너 보장 ===
try:
    blob_service_client.create_container(AZURE_STORAGE_CONTAINER_NAME)
except Exception:
    pass

# === Streamlit 페이지 설정 ===
st.set_page_config(page_title="RAG 데이터 구성", layout="wide")
st.title("📘 RAG 데이터 구성")

# --- 1️⃣ 문서 업로드 ---
st.markdown("#### 📤 문서 업로드")
uploaded_file = st.file_uploader("TXT 형식의 문서를 업로드하세요", type=["txt"], label_visibility="collapsed")

if uploaded_file:
    blob_client = blob_service_client.get_blob_client(container=AZURE_STORAGE_CONTAINER_NAME, blob=uploaded_file.name)
    blob_client.upload_blob(uploaded_file.getvalue(), overwrite=True)
    st.success(f"✅ '{uploaded_file.name}' 업로드 완료!")

# --- 2️⃣ 업로드된 문서 목록 ---
st.markdown("#### 📂 업로드된 문서 목록")
container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER_NAME)
blobs = list(container_client.list_blobs())

if not blobs:
    st.info("현재 업로드된 파일이 없습니다.")
else:
    filenames = [blob.name for blob in blobs]
    selected_file = st.selectbox("인덱싱할 파일을 선택하세요", filenames)
    col1, col2 = st.columns([1, 0.2])
    with col1:
        index_btn = st.button("🔍 선택 파일 인덱싱 시작")
    with col2:
        if st.button("🗑 파일 삭제"):
            blob_client = container_client.get_blob_client(selected_file)
            blob_client.delete_blob()
            st.warning(f"'{selected_file}' 삭제 완료!")
            st.rerun()

# --- 3️⃣ 인덱싱 ---
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = set()

if 'index_btn' in locals() and index_btn:
    st.markdown("### ⚙️ 인덱싱 진행 중...")

    index_client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_key))

    # === 최신 스펙 반영된 필드 정의 ===
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile"
        ),
    ]

    # === Vector Search 구성 ===
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw-config")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw-config")]
    )

    # === 인덱스 생성 ===
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search
    )

    index_client.create_or_update_index(index)

    # === 문서 읽기 및 임베딩 처리 ===
    blob_data = container_client.download_blob(selected_file).readall().decode("utf-8")
    chunks = [blob_data[i:i+2000] for i in range(0, len(blob_data), 2000)]
    search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AzureKeyCredential(search_key))

    progress = st.progress(0)
    docs = []
    for i, chunk in enumerate(chunks):
        embedding = openai_client.embeddings.create(
            model=DEPLOYMENT_EMBEDDING_NAME,
            input=chunk
        ).data[0].embedding

        docs.append({
            "id": str(uuid.uuid4()),
            "content": chunk,
            "source": selected_file,
            "embedding": embedding
        })
        progress.progress((i + 1) / len(chunks))
        time.sleep(0.05)

    search_client.upload_documents(docs)
    st.success(f"✅ {selected_file} 인덱싱 완료! ({len(docs)}개 섹션)")
    st.session_state.indexed_files.add(selected_file)

# --- 4️⃣ 질의응답 (RAG) ---
st.markdown("#### 💬 질의응답 테스트")
query = st.text_input("질문을 입력하세요", placeholder="예: ISO 25010에서 기능적 적합성이란 무엇인가요?")
if st.button("🔎 답변 생성"):
    if not query:
        st.warning("질문을 입력해주세요.")
    else:
        with st.spinner("🔎 검색 및 LLM 응답 생성 중..."):
            search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AzureKeyCredential(search_key))
            embedding = openai_client.embeddings.create(
                model=DEPLOYMENT_EMBEDDING_NAME,
                input=query
            ).data[0].embedding

            results = search_client.search(
                search_text=None,
                vector_queries=[{
                    "kind": "vector",
                    "vector": embedding,
                    "fields": "embedding",
                    "k": 3
                }],
                select=["content", "source"]
            )

            sources, context_chunks = [], []
            for doc in results:
                context_chunks.append(doc["content"])
                sources.append(doc["source"])

            context = "\n\n".join(context_chunks)
            prompt = f"""
            다음은 ISO 25010 문서의 일부 내용입니다:

            {context}

            질문: {query}
            ISO 25010 기준에 따라 명확하고 간결하게 한국어로 설명해주세요.
            """

            response = openai_client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content

        st.subheader("🧠 답변")
        st.write(answer)

        with st.expander("📖 참조된 문서"):
            for src in set(sources):
                st.markdown(f"- `{src}`")
