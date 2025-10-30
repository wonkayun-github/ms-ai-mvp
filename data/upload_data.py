"""
변환된 ISO 25010 데이터를 Azure AI Search에 업로드
"""

import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

load_dotenv()

# 환경 변수
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = "iso25010-optimized"

def upload_documents(documents):
    """문서를 Azure AI Search에 업로드"""
    
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )
    
    try:
        # 배치 업로드
        result = search_client.upload_documents(documents=documents)
        
        success_count = sum(1 for r in result if r.succeeded)
        fail_count = len(result) - success_count
        
        print(f"✅ 업로드 완료:")
        print(f"   - 성공: {success_count}개")
        print(f"   - 실패: {fail_count}개")
        
        # 실패한 문서 출력
        if fail_count > 0:
            print("\n❌ 실패한 문서:")
            for r in result:
                if not r.succeeded:
                    print(f"   - {r.key}: {r.error_message}")
        
        return success_count, fail_count
        
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")
        return 0, len(documents)

def verify_upload(expected_count):
    """업로드 검증"""
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )
    
    try:
        # 전체 문서 수 확인
        results = search_client.search(
            search_text="*",
            include_total_count=True,
            top=0
        )
        
        actual_count = results.get_count()
        print(f"\n✅ 검증 완료:")
        print(f"   - 예상 문서 수: {expected_count}개")
        print(f"   - 실제 문서 수: {actual_count}개")
        
        if actual_count == expected_count:
            print("   ✅ 모든 문서가 정상적으로 업로드되었습니다!")
        else:
            print(f"   ⚠️ 문서 수 불일치 ({expected_count - actual_count}개 차이)")
        
        return actual_count
        
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return 0

def test_search():
    """검색 테스트"""
    credential = AzureKeyCredential(AZURE_SEARCH_KEY)
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )
    
    print("\n🔍 검색 테스트:")
    
    # 테스트 쿼리들
    test_queries = [
        "시스템이 필요한 모든 기능을 제공합니까?",
        "응답 속도가 빠릅니까?",
        "보안"
    ]
    
    for query in test_queries:
        print(f"\n쿼리: '{query}'")
        try:
            results = search_client.search(
                search_text=query,
                top=3,
                select=["quality_characteristic", "sub_characteristic", "doc_type"],
                filter="doc_type eq 'sub_characteristic'"
            )
            
            print("결과:")
            for i, result in enumerate(results, 1):
                quality = result.get("quality_characteristic", "")
                sub = result.get("sub_characteristic", "")
                print(f"  {i}. {quality} > {sub}")
                
        except Exception as e:
            print(f"  ❌ 검색 실패: {e}")

if __name__ == "__main__":
    print("📤 Azure AI Search 데이터 업로드 시작...\n")
    
    # 1. JSON 파일 로드
    json_file = "./data/iso25010_documents.json"
    
    if not os.path.exists(json_file):
        print(f"❌ 파일을 찾을 수 없습니다: {json_file}")
        print("먼저 convert_iso25010.py를 실행하세요.")
        exit(1)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"📄 {len(documents)}개 문서 로드 완료")
    
    # 2. 업로드
    success, fail = upload_documents(documents)
    
    if fail > 0:
        print("\n⚠️ 일부 문서 업로드 실패")
        exit(1)
    
    # 3. 검증
    verify_upload(len(documents))
    
    # 4. 검색 테스트
    test_search()
    
    print("\n✅ 모든 작업 완료!")
    print("\n다음 단계:")
    print("1. .env 파일에서 AZURE_SEARCH_INDEX를 'iso25010-optimized'로 변경")
    print("2. app_with_rag.py의 search_appropriate_quality_attribute 함수 업데이트")
    print("3. 애플리케이션 테스트")