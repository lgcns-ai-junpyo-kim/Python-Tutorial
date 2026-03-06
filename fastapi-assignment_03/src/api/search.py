"""DAP 벡터 DB 검색 API 라우터.

이 파일의 목적:
- DAP 검색 API를 직접 호출해 문서를 반환하는 엔드포인트를 제공합니다.

포함 내용:
- `POST /api/v1/search` 라우터

사용 시점:
- Swagger에서 DAP 검색 결과를 직접 확인할 때 사용합니다.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from src.models.chat import RagDocument
from src.services.retrieval.dap_rag_retriever import dap_rag_documents

router = APIRouter(prefix="/api/v1", tags=["search"])


class SearchRequest(BaseModel):
    question: str
    access_key: str | None = None
    collection_alias: str | None = None
    topk: int = 5
    hybrid_yn: bool = True
    alpha: float = 0.5


class SearchResponse(BaseModel):
    data: list[RagDocument]


@router.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    """DAP 벡터 DB에서 관련 문서를 검색합니다."""
    documents = dap_rag_documents(
        question=request.question,
        req_access_key=request.access_key,
        req_collection_alias=request.collection_alias,
        topk=request.topk,
        hybrid_yn=request.hybrid_yn,
        alpha=request.alpha,
    )
    return SearchResponse(data=documents)
