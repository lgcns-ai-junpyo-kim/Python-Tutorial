"""RAG 목업 문서 저장소.

이 파일의 목적:
- RAG 분기에서 사용할 문서(DAP 에서 검색된 문서)를 제공합니다.

포함 내용:
- dap_rag_documents 함수

사용 시점:
- 검색기를 통과한 후 분기 흐름과 응답 포맷을 검증할 때 사용합니다.
"""
import logging
import os
import requests
from src.models.chat import RagDocument

logger = logging.getLogger(__name__)

VECTOR_DB_URL = os.getenv("VECTOR_DB_PATH") or "http://35.216.126.198:30870/api/v1/search/vectordb"
ACCESS_KEY = os.getenv("ACCESS_KEY") or "9507640340643580a33665b9e2d214d28cabb8bd7926b1c930229b6bc6e38abb"
COLLECTION_ALIAS = os.getenv("COLLECTION_ALIAS") or "PJT20260025_pipeline_test_kjp"

def dap_rag_documents(
    question: str,
    access_key: str | None = None,
    collection_alias: str | None = None,
    topk: int = 5,
    hybrid_yn: bool = True,
    alpha: float = 0.5,
) -> list[RagDocument]:
    """
    DAP 검색 API 응답을 RagDocument 리스트로 변환합니다.

    Parameters:
        question: 검색 질문
        req_access_key: DAP 액세스 키 (None이면 환경변수 사용)
        req_collection_alias: 컬렉션 alias (None이면 환경변수 사용)
        topk: 검색 결과 수
        hybrid_yn: 하이브리드 검색 여부
        alpha: 하이브리드 검색 가중치

    Returns:
        list[RagDocument]
    """
    payload = {
        "access_key": access_key or ACCESS_KEY,
        "collection_alias": collection_alias or COLLECTION_ALIAS,
        "question": question,
        "topK": topk,
        "hybrid_yn": hybrid_yn,
        "alpha": alpha,
    }

    response = requests.post(VECTOR_DB_URL, json=payload, timeout=10)
    if not response.ok:
        logger.error(
            "DAP API error status=%s body=%s",
            response.status_code,
            response.text[:500],
        )
    response.raise_for_status()
    body = response.json()
    results = body.get("data", []) if isinstance(body, dict) else body

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
