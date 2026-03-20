from router_p.providers.types import ProviderChatResponse


class StubProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Stub local reply",
            prompt_tokens=3,
            completion_tokens=3,
            raw_model=request.model,
        )


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


def test_chat_completions_rejects_streaming_requests(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Streaming is not supported yet"


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
