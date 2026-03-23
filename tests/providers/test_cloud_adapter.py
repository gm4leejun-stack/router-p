import json

import httpx
import pytest

from router_p.api.schemas.chat import ChatMessage
from router_p.providers.cloud import OpenAICompatibleCloudProvider
from router_p.providers.types import ProviderChatRequest


def test_cloud_provider_sends_openai_compatible_request_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-cloud-key"
        payload = json.loads(request.content.decode())
        assert payload["model"] == "gpt-general"
        assert payload["stream"] is False
        return httpx.Response(
            200,
            json={
                "model": "gpt-general",
                "choices": [{"message": {"role": "assistant", "content": "Cloud hello"}}],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 2,
                    "total_tokens": 7,
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://cloud.test")
    provider = OpenAICompatibleCloudProvider(
        base_url="http://cloud.test",
        api_key="test-cloud-key",
        client=client,
    )

    response = provider.complete(
        ProviderChatRequest(
            model="gpt-general",
            messages=[ChatMessage(role="user", content="Hello")],
            timeout_seconds=30.0,
        )
    )

    assert response.content == "Cloud hello"
    assert response.prompt_tokens == 5
    assert response.completion_tokens == 2
    assert response.raw_model == "gpt-general"


def test_cloud_provider_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://cloud.test")
    provider = OpenAICompatibleCloudProvider(
        base_url="http://cloud.test",
        api_key="test-cloud-key",
        client=client,
    )

    with pytest.raises(RuntimeError, match="Cloud request failed"):
        provider.complete(
            ProviderChatRequest(
                model="gpt-general",
                messages=[ChatMessage(role="user", content="Hello")],
                timeout_seconds=30.0,
            )
        )
