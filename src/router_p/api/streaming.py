import json

from router_p.providers.types import ProviderStreamChunk


def format_sse_chunk(chunk: ProviderStreamChunk, chunk_id: str) -> str:
    payload = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "model": chunk.raw_model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": chunk.content_delta},
                "finish_reason": None,
            }
        ],
    }
    return f"data: {json.dumps(payload)}\n\n"


def format_sse_done() -> str:
    return "data: [DONE]\n\n"
