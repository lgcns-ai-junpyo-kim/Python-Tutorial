"""RAG 목업 문서 저장소.

이 파일의 목적:
- RAG 분기에서 사용할 문서(DAP 에서 검색된 문서)를 제공합니다.

포함 내용:
- dap_rag_documents 함수

사용 시점:
- 검색기를 통과한 후 분기 흐름과 응답 포맷을 검증할 때 사용합니다.
"""
import os
import requests
from src.models.chat import RagDocument

vector_db_url = os.getenv("VECTOR_DB_PATH") or "http://35.216.126.198:30870/api/v1/search/vectordb"
access_key = os.getenv("ACCESS_KEY") or "9507640340643580a33665b9e2d214d28cabb8bd7926b1c930229b6bc6e38abb"
collection_alias = os.getenv("COLLECTION_ALIAS") or "PJT20260025_pipeline_test_kjp"

def dap_rag_documents(question: str) -> list[RagDocument]:
    """
    DAP 검색 API 응답을 RagDocument 리스트로 변환합니다.

    Parameters:
        search_response: DAP 검색 API의 JSON 응답(dict)

    Returns:
        list[RagDocument]
    """
    payload = {
        "access_key": access_key,
        "collection_alias": collection_alias,
        "question": question,
        "topK": 5,         
        "hybrid_yn": True,
        "alpha": 0.5,
    }

    response = requests.post(vector_db_url, json=payload, timeout=10)
    response.raise_for_status()
    results = response.json()
    
    documents: list[RagDocument] = []

    for result in results:
        if not isinstance(result, dict):
            continue

        title = str(result.get("title", ""))
        content = str(result.get("content", ""))
        page = result.get("page_number", result.get("page", 0))

        try:
            page_number = int(page) if page is not None else 0
        except (ValueError, TypeError):
            page_number = 0

        documents.append(
            RagDocument(
                title=title,
                content=content,
                page_number=page_number,
            )
        )

    return documents
