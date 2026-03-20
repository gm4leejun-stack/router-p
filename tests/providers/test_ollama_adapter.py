import json

import httpx
import pytest

from router_p.api.schemas.chat import ChatMessage
from router_p.providers.ollama import OllamaChatProvider
from router_p.providers.types import ProviderChatRequest, ProviderChatResponse


def test_provider_chat_request_accepts_model_messages_and_timeout():
    request = ProviderChatRequest(
        model="qwen3:4b",
        messages=[ChatMessage(role="user", content="Hello")],
        timeout_seconds=30.0,
    )

    assert request.model == "qwen3:4b"
    assert request.timeout_seconds == 30.0


def test_provider_chat_response_holds_normalized_result_fields():
    response = ProviderChatResponse(
        content="Hello back",
        prompt_tokens=3,
        completion_tokens=2,
        raw_model="qwen3:4b",
    )

    assert response.content == "Hello back"
    assert response.raw_model == "qwen3:4b"


def test_ollama_provider_sends_chat_request_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content.decode())
        assert payload["model"] == "qwen3:4b"
        assert payload["stream"] is False
        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b",
                "message": {"role": "assistant", "content": "Hello back"},
                "prompt_eval_count": 3,
                "eval_count": 2,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama.test")
    provider = OllamaChatProvider(client=client, base_url="http://ollama.test")

    response = provider.complete(
        ProviderChatRequest(
            model="qwen3:4b",
            messages=[ChatMessage(role="user", content="Hello")],
            timeout_seconds=30.0,
        )
    )

    assert response.content == "Hello back"
    assert response.prompt_tokens == 3
    assert response.completion_tokens == 2


def test_ollama_provider_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama.test")
    provider = OllamaChatProvider(client=client, base_url="http://ollama.test")

    with pytest.raises(RuntimeError, match="Ollama request failed"):
        provider.complete(
            ProviderChatRequest(
                model="qwen3:4b",
                messages=[ChatMessage(role="user", content="Hello")],
                timeout_seconds=30.0,
            )
        )
