from fastapi.testclient import TestClient

from router_p.app import create_app
from router_p.config import Settings
from router_p.providers.types import ProviderChatResponse, ProviderStreamChunk


class StubProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Deployment hello",
            prompt_tokens=4,
            completion_tokens=2,
            raw_model=request.model,
        )

    def stream_complete(self, request):
        yield ProviderStreamChunk(content_delta="De", raw_model=request.model)
        yield ProviderStreamChunk(content_delta="ploy", raw_model=request.model)


class FailingCloudProvider:
    def complete(self, request):
        raise RuntimeError("cloud failed")

    def stream_complete(self, request):
        raise RuntimeError("cloud failed")


def make_client() -> TestClient:
    settings = Settings(api_key="test-router-p-key")
    return TestClient(create_app(settings))


def test_deployment_health_returns_ready_metadata():
    client = make_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "router-p",
        "status": "ready",
        "environment": "development",
    }


def test_deployment_protected_routes_return_stable_auth_error():
    client = make_client()

    response = client.post(
        "/chat/completions",
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Unauthorized",
            "type": "auth_error",
        }
    }


def test_deployment_chat_returns_openai_style_non_stream_response(monkeypatch):
    client = make_client()
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )

    response = client.post(
        "/chat/completions",
        headers={"Authorization": "Bearer test-router-p-key"},
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == "Deployment hello"
    assert body["usage"]["total_tokens"] == 6


def test_deployment_chat_returns_sse_stream_with_done_marker(monkeypatch):
    client = make_client()
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )

    response = client.post(
        "/chat/completions",
        headers={"Authorization": "Bearer test-router-p-key"},
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"De"' in response.text
    assert "data: [DONE]" in response.text


def test_deployment_provider_failures_return_stable_error_shape(monkeypatch):
    client = make_client()
    client.app.state.settings.cloud_general_model = "gpt-general"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: FailingCloudProvider(),
    )

    response = client.post(
        "/chat/completions",
        headers={"Authorization": "Bearer test-router-p-key"},
        json={
            "model": "gpt-general",
            "messages": [{"role": "user", "content": "Hello cloud"}],
            "stream": False,
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "provider_error",
            "message": "cloud failed",
            "type": "provider_error",
        }
    }
