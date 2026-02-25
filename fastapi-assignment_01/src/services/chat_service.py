"""채팅 도메인 서비스.

이 파일의 목적:
- 채팅 응답 생성 비즈니스 로직을 제공합니다.

포함 내용:
- generate_chat_response 함수 자리

사용 시점:
- 실습에서 서비스 레이어를 직접 구현할 때 사용합니다.
"""
from src.models.chat import ChatRequest, ChatResponse

class ChatService:
    """채팅 요청을 처리하는 서비스."""

    def generate_chat_response(self, request: ChatRequest) -> ChatResponse:
        """채팅 요청을 처리한다.

        Args:
            request: 채팅 요청 데이터.

        Returns:
            ChatResponse: 입력에 대한 결과 응답.
        """
        return ChatResponse(message="답변이 생성되었습니다.")