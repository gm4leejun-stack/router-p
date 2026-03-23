from router_p.providers.types import ProviderChatResponse, ProviderStreamChunk


class StubProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Stub local reply",
            prompt_tokens=3,
            completion_tokens=3,
            raw_model=request.model,
        )

    def stream_complete(self, request):
        yield ProviderStreamChunk(content_delta="Hel", raw_model=request.model)
        yield ProviderStreamChunk(content_delta="lo", raw_model=request.model)


class StubCloudProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Stub cloud reply",
            prompt_tokens=5,
            completion_tokens=4,
            raw_model=request.model,
        )

    def stream_complete(self, request):
        yield ProviderStreamChunk(content_delta="Clo", raw_model=request.model)
        yield ProviderStreamChunk(content_delta="ud", raw_model=request.model)


class StubBoundaryProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="local_text",
            prompt_tokens=2,
            completion_tokens=1,
            raw_model=request.model,
        )


class FailingLocalProvider:
    def complete(self, request):
        raise RuntimeError("local failed")


class FailingCloudProvider:
    def complete(self, request):
        raise RuntimeError("cloud failed")

    def stream_complete(self, request):
        raise RuntimeError("cloud failed")


def test_chat_completions_requires_api_key(client):
    response = client.post(
        "/chat/completions",
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 401


def test_chat_completions_returns_non_stream_response(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["model"] == "qwen3:4b"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == "Stub local reply"
    assert body["usage"]["total_tokens"] >= body["usage"]["completion_tokens"]


def test_chat_completions_streams_local_responses(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "chat.completion.chunk" in response.text
    assert '"Hel"' in response.text
    assert "data: [DONE]" in response.text


def test_chat_completions_validates_message_shape(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={"model": "qwen3:4b", "messages": [{"role": "tool", "content": "bad"}]},
    )

    assert response.status_code == 422


def test_chat_completions_routes_router_auto_code_requests(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Refactor this Python function"}],
            "stream": False,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["model"] == "qwen2.5-coder:7b"
    assert body["choices"][0]["message"]["content"] == "Stub local reply"


def test_chat_completions_routes_simple_text_requests_to_local_text(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Write a short welcome message"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "qwen3:4b"
    assert response.json()["choices"][0]["message"]["content"] == "Stub local reply"


def test_chat_completions_routes_complex_general_requests_to_cloud(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: StubCloudProvider(),
    )
    client.app.state.settings.cloud_general_model = "gpt-general"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Compare three architectures and migration strategy"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-general"
    assert response.json()["choices"][0]["message"]["content"] == "Stub cloud reply"


def test_chat_completions_routes_complex_code_requests_to_cloud(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: StubCloudProvider(),
    )
    client.app.state.settings.cloud_code_model = "gpt-code"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Multi-file codebase refactor and deep debugging plan"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-code"
    assert response.json()["choices"][0]["message"]["content"] == "Stub cloud reply"


def test_chat_completions_uses_explicit_cloud_model(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: StubCloudProvider(),
    )
    client.app.state.settings.cloud_general_model = "gpt-general"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "gpt-general",
            "messages": [{"role": "user", "content": "Hello cloud"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-general"
    assert response.json()["choices"][0]["message"]["content"] == "Stub cloud reply"


def test_chat_completions_boundary_requests_use_boundary_classifier(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    monkeypatch.setattr(
        "router_p.services.boundary_classifier.OllamaChatProvider",
        lambda **kwargs: StubBoundaryProvider(),
    )

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Help me figure out the best model for this"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "qwen3:4b"
    assert response.json()["choices"][0]["message"]["content"] == "Stub local reply"


def test_chat_completions_falls_back_to_cloud_when_local_provider_fails(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: FailingLocalProvider(),
    )
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: StubCloudProvider(),
    )
    client.app.state.settings.cloud_general_model = "gpt-general"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "gpt-general"
    assert response.json()["choices"][0]["message"]["content"] == "Stub cloud reply"


def test_chat_completions_streams_cloud_responses(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OllamaChatProvider",
        lambda **kwargs: StubProvider(),
    )
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: StubCloudProvider(),
    )
    client.app.state.settings.cloud_general_model = "gpt-general"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "gpt-general",
            "messages": [{"role": "user", "content": "Hello cloud"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"Clo"' in response.text
    assert "data: [DONE]" in response.text


def test_chat_completions_wraps_provider_failures_with_stable_error_shape(
    client,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        "router_p.services.chat_completion.OpenAICompatibleCloudProvider",
        lambda **kwargs: FailingCloudProvider(),
    )
    client.app.state.settings.cloud_general_model = "gpt-general"
    client.app.state.settings.cloud_api_key = "test-cloud-key"
    client.app.state.settings.cloud_base_url = "http://cloud.test"

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
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
