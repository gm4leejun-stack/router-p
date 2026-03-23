import json

import httpx

from router_p.api.streaming import format_sse_chunk, format_sse_done
from router_p.api.schemas.chat import ChatMessage
from router_p.providers.cloud import OpenAICompatibleCloudProvider
from router_p.providers.ollama import OllamaChatProvider
from router_p.providers.types import ProviderChatRequest, ProviderStreamChunk
from router_p.providers.types import ProviderStreamChunk


def test_provider_stream_chunk_holds_delta_content():
    chunk = ProviderStreamChunk(content_delta="Hello", raw_model="qwen3:4b")

    assert chunk.content_delta == "Hello"
    assert chunk.raw_model == "qwen3:4b"


def test_format_sse_chunk_emits_openai_style_data_frame():
    chunk = ProviderStreamChunk(content_delta="Hello", raw_model="qwen3:4b")

    payload = format_sse_chunk(chunk, chunk_id="chatcmpl-test")

    assert payload.startswith("data: ")
    assert "\"chat.completion.chunk\"" in payload
    assert "\"Hello\"" in payload


def test_format_sse_done_emits_done_marker():
    assert format_sse_done() == "data: [DONE]\n\n"


def test_ollama_stream_complete_translates_json_lines():
    def handler(request: httpx.Request) -> httpx.Response:
        body = b'{"message":{"content":"Hel"},"model":"qwen3:4b"}\n{"message":{"content":"lo"},"model":"qwen3:4b"}\n'
        return httpx.Response(200, content=body)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama.test")
    provider = OllamaChatProvider(base_url="http://ollama.test", client=client)

    chunks = list(
        provider.stream_complete(
            ProviderChatRequest(
                model="qwen3:4b",
                messages=[ChatMessage(role="user", content="Hello")],
                timeout_seconds=30.0,
            )
        )
    )

    assert [chunk.content_delta for chunk in chunks] == ["Hel", "lo"]


def test_cloud_stream_complete_translates_sse_lines():
    def handler(request: httpx.Request) -> httpx.Response:
        body = (
            b'data: {"model":"gpt-general","choices":[{"delta":{"content":"Hel"}}]}\n\n'
            b'data: {"model":"gpt-general","choices":[{"delta":{"content":"lo"}}]}\n\n'
            b'data: [DONE]\n\n'
        )
        return httpx.Response(200, content=body)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://cloud.test")
    provider = OpenAICompatibleCloudProvider(
        base_url="http://cloud.test",
        api_key="test-cloud-key",
        client=client,
    )

    chunks = list(
        provider.stream_complete(
            ProviderChatRequest(
                model="gpt-general",
                messages=[ChatMessage(role="user", content="Hello")],
                timeout_seconds=30.0,
            )
        )
    )

    assert [chunk.content_delta for chunk in chunks] == ["Hel", "lo"]
