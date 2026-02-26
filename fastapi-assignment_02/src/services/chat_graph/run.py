"""채팅 그래프 실행기.

이 파일의 목적:
- 그래프 실행 결과를 non-streaming 응답과 SSE 스트리밍으로 변환합니다.

포함 내용:
- resolve_message 함수
- stream_sse_events_from_graph 함수

사용 시점:
- 오케스트레이션 서비스에서 그래프 실행 결과를 소비할 때 사용합니다.
"""

import json
from collections.abc import Iterator

from src.services.chat_graph.state import BranchStreamState
from src.services.chat_graph.builder import build_stream_graph

STREAM_GRAPH = build_stream_graph()

def resolve_message(message: str) -> str:
    """non-streaming용 최종 메시지를 반환합니다."""
    # Step 1. message를 이용해 초기 상태를 구성합니다.
    # Step 2. STREAM_GRAPH.invoke(...)로 그래프를 끝까지 실행합니다.
    # Step 3. 최종 상태에서 final_message를 꺼내 반환합니다.
    state = BranchStreamState(
        user_input = message,
        final_message = "",
        cursor = 0,
        delta = ""
    )

    final_state = STREAM_GRAPH.invoke(state)
    return final_state["final_message"]

def _sse(payload: dict) -> str:
    """테스트가 파싱하는 data 라인만 만들어 반환합니다."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

def stream_sse_events_from_graph(message: str) -> Iterator[str]:
    """그래프 업데이트를 SSE 이벤트로 직렬화해 반환합니다."""
    # Step 1. message를 이용해 초기 상태를 구성합니다.
    # Step 2. STREAM_GRAPH.stream(..., stream_mode='updates')를 순회합니다.
    # Step 3. emit_chunk 업데이트마다 chunk 이벤트를 yield 합니다.
    # Step 4. 마지막에 final 이벤트를 1회 yield 합니다.
    state = BranchStreamState(
        user_input = message,
        final_message = "",
        cursor = 0,
        delta = ""
    )
    
    chunks: list[str] = []

    for update in STREAM_GRAPH.stream(state, stream_mode="updates"):
        delta = ""
        if isinstance(update, dict):
            # update: {"EmitChunkNode": {"delta": "A", "cursor": 1, ...}}
            for _, payload in update.items():
                if isinstance(payload, dict) and isinstance(payload.get("delta"), str):
                    delta = payload["delta"]
                    break

        # Step 3. emit_chunk 업데이트마다 chunk 이벤트를 yield
        if delta:
            chunks.append(delta)
            yield _sse({"type": "chunk", "delta": delta})

    # Step 4. 마지막에 final 이벤트를 1회 yield
    final_message = "".join(chunks)
    yield _sse({"type": "final", "message": final_message})