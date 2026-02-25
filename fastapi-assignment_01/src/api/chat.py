"""채팅 API 라우터.

이 파일의 목적:
- `/api/v1/chat` 엔드포인트 라우팅을 제공합니다.

포함 내용:
- POST `/api/v1/chat` 라우트 자리

사용 시점:
- 실습에서 FastAPI 라우터를 직접 구현할 때 사용합니다.
"""

"""채팅 API 라우터 모듈."""

from fastapi import APIRouter
from src.models.chat import ChatRequest, ChatResponse
from src.services.chat_service import ChatService

API_V1_PREFIX = "/api/v1"
CHAT_PREFIX = "/chat"

class ChatRouter:
    """채팅 API 라우터를 구성한다."""

    def __init__(self, service: ChatService) -> None:
        """라우터와 의존성을 초기화한다.

        Args:
            service: 채팅 서비스.
        """
        self.service = service
        self.router = APIRouter(
            prefix = API_V1_PREFIX
        )
        self.router.add_api_route(
            path = CHAT_PREFIX,
            endpoint = self.chat,
            methods = ["POST"],
            response_model =  ChatResponse,
            summary = "Chat",
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        """입력 요청을 처리한다.

        Args:
            request: 요청 데이터.

        Returns:
            ChatResponse: 응답 결과.
        """
        result = self.service.generate_chat_response(request)
        return result


_router = ChatRouter(ChatService())
router = _router.router