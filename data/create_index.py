"""
Azure AI Search 인덱스 생성 스크립트
ISO 25010 품질 속성 검색을 위한 최적화된 인덱스 생성
"""

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    ComplexField
)
from dotenv import load_dotenv

load_dotenv()

# 환경 변수
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = "iso25010-optimized"

def create_index():
    """ISO 25010 최적화 인덱스 생성"""
    
    # 클라이언트 생성
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    index_client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=credential
    )
    
    # 필드 정의
    fields = [
        # 기본 필드
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True
        ),
        
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="ko.lucene",  # 한국어 분석기
            searchable=True
        ),
        
        # 계층 구조 필드
        SearchableField(
            name="quality_characteristic",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
            searchable=True
        ),
        
        SearchableField(
            name="sub_characteristic",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
            searchable=True
        ),
        
        # 영어명
        SearchableField(
            name="quality_characteristic_en",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        
        SearchableField(
            name="sub_characteristic_en",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        
        # 문서 타입 (main_characteristic / sub_characteristic)
        SimpleField(
            name="doc_type",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        
        # 계층 레벨
        SimpleField(
            name="level",
            type=SearchFieldDataType.Int32,
            filterable=True
        ),
        
        # 검색 향상 필드
        SearchableField(
            name="keywords",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True
        ),
        
        SearchableField(
            name="example_questions",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            searchable=True
        ),
        
        # 관계 필드
        SimpleField(
            name="parent_id",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        
        # 메타데이터
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        
        SearchableField(
            name="definition",
            type=SearchFieldDataType.String,
            searchable=True
        )
    ]
    
    # 인덱스 생성
    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields
    )
    
    try:
        result = index_client.create_or_update_index(index)
        print(f"✅ 인덱스 생성 완료: {result.name}")
        print(f"   - 필드 수: {len(result.fields)}")
        return True
    except Exception as e:
        print(f"❌ 인덱스 생성 실패: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Azure AI Search 인덱스 생성 시작...")
    success = create_index()
    
    if success:
        print("\n✅ 인덱스 생성 완료!")
        print(f"   인덱스명: {INDEX_NAME}")
        print("\n다음 단계:")
        print("1. 데이터 준비 (prepare_data.py)")
        print("2. 데이터 업로드 (upload_data.py)")
    else:
        print("\n❌ 인덱스 생성 실패")
        print("   환경 변수를 확인해주세요:")
        print("   - AZURE_SEARCH_ENDPOINT")
        print("   - AZURE_SEARCH_KEY")
