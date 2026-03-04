"""LangChain BaseChatModel 기반 원격 LLM 모델.

이 파일의 목적:
- 외부 chat completions 엔드포인트를 BaseChatModel 인터페이스로 감쌉니다.

포함 내용:
- EndpointChatModel 클래스

사용 시점:
- 게이트웨이에서 LLM 호출을 표준 ChatModel 방식으로 처리할 때 사용합니다.
"""

from collections.abc import Iterator
import json
import logging
from typing import Any

import httpx
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

from src.core.errors import UpstreamServiceError
from src.services.llm_parsing import extract_text_from_stream_chunk

logger = logging.getLogger(__name__)


class EndpointChatModel(BaseChatModel):
    """외부 엔드포인트를 호출하는 BaseChatModel 구현."""

    endpoint: str
    model_name: str
    request_timeout: float = 30.0
    default_temperature: float = 0.6
    default_max_tokens: int = 200
    headers: dict[str, str] = Field(
        default_factory=lambda: {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    @property
    def _llm_type(self) -> str:
        """모델 타입 식별자를 반환합니다."""
        return "endpoint-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """non-stream chat completion을 실행합니다."""
        del stop, run_manager
        payload = self._build_payload(messages=messages, stream=False, **kwargs)
        response_json = self._post_json(payload)
        content = self._extract_completion_text(response_json)
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=content))],
            llm_output={"raw_response": response_json},
        )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """stream chat completion을 실행합니다."""
        del stop
        # Step 1. `_build_payload(..., stream=True)`로 요청 본문을 만드세요.
        # Step 2. `httpx.Client().stream(...)`으로 SSE 라인을 순회하세요.
        # Step 3. `data:` 라인을 파싱해 delta를 추출하고 ChatGenerationChunk를 yield 하세요.
        # Step 4. HTTP/JSON 예외를 UpstreamServiceError로 변환하세요.
        payload = self._build_payload(messages=messages, stream=True, **kwargs)
        try:
            with httpx.Client(timeout=self.request_timeout) as Client:
                with Client.stream(
                    "POST",
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                ) as response:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        body_snippet = (response.text or "")[:500]
                        logger.error(
                            "LLM stream HTTP error status=%s body=%s",
                            response.status_code,
                            body_snippet
                        )
                    # 라인 순회
                    for line in response.iter_lines():
                        if not line:
                            continue
                        # 라인 파싱
                        raw_line = line.strip()

                        if raw_line.startswith("data:"):
                            raw_line = raw_line[len("data:"):].strip()

                        if raw_line in {"[DONE]", "DONE"}:
                            break

                        try:
                            chunk_json = json.loads(raw_line)
                        except json.JSONDecodeError as e:
                            logger.error(
                                "LLM stream HTTP error line=%s",
                                raw_line[:500]
                            )
                            raise UpstreamServiceError(
                                "LLM stream JSON decode error"
                            ) from e
                        
                        delta_text = extract_text_from_stream_chunk(chunk_json)
                        if not delta_text:
                            continue

                        if run_manager is not None:
                            run_manager.on_llm_new_token(delta_text)

                        yield ChatGenerationChunk(message=AIMessageChunk(content=delta_text))

        # HTTP/JSON 예외를 UpstreamServiceError로 변환
        except UpstreamServiceError:
            raise
        except (httpx.HTTPError, OSError) as e:
            logger.exception("LLM stream upstream error: %s", e)
            raise UpstreamServiceError("LLM stream upstream error") from e


    def _build_payload(
        self,
        messages: list[BaseMessage],
        stream: bool,
        **kwargs: Any,
    ) -> dict[str, object]:
        """엔드포인트 요청 payload를 생성합니다."""
        # Step 1. temperature/max_tokens 기본값을 처리하세요.
        # Step 2. LangChain 메시지를 OpenAI 호환 dict(role/content)로 변환하세요.
        # Step 3. stream/model 필드를 포함한 payload를 반환하세요.
        temperature = kwargs.get("temperature", self.default_temperature)
        max_tokens = kwargs.get("max_tokens", self.default_max_tokens)
        
        temperature = float(temperature)
        max_tokens = int(max_tokens)

        openai_messages = [self._to_openai_message(m) for m in messages]

        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": openai_messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        return payload


    def _post_json(self, payload: dict[str, object]) -> dict[str, object]:
        """JSON 응답을 반환하는 POST 호출을 수행합니다."""
        # Step 1. httpx.post로 엔드포인트를 호출하세요.
        # Step 2. raise_for_status + response.json 처리하세요.
        # Step 3. HTTPStatusError/JSONDecodeError/HTTPError를 로깅 후 UpstreamServiceError로 변환하세요.
        try:
            with httpx.Client(timeout=self.request_timeout) as client:
                response = client.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload
                )

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    body_snippet = (response.text or "")[:500]
                    logger.error(
                        "LLM HTTP error status=%s body=%s",
                        response.status_code,
                        body_snippet,
                    )
                    raise UpstreamServiceError("LLM HTTP error") from e
                
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    body_snippet = (response.text or "")[:500]
                    logger.error("LLM JSON decode error body=%s", body_snippet)
                    raise UpstreamServiceError("LLM JSON decode error") from e
                
                if not isinstance(data, dict):
                    logger.error("LLM response is not a JSON object type=%s", type(data))
                    raise UpstreamServiceError("LLM invalid JSON response")
                
                return data
        except UnboundLocalError:
            raise
        except httpx.HTTPError as e:
            logger.exception("LLM upstream HTTP error: %s", e)
            raise UpstreamServiceError("LLM upstream HTTP error") from e
        

    def _extract_completion_text(self, payload: dict[str, object]) -> str:
        """completion 응답에서 텍스트를 추출합니다."""
        choices = payload.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            first = choices[0]
            message = first.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
            text = first.get("text")
            if isinstance(text, str):
                return text
        return ""

    def _to_openai_message(self, message: BaseMessage) -> dict[str, str]:
        """LangChain 메시지를 OpenAI 호환 role/content로 변환합니다."""
        role = message.type
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
        elif role not in {"system", "user", "assistant"}:
            role = "user"
        content = message.content if isinstance(message.content, str) else str(message.content)
        return {"role": role, "content": content}

