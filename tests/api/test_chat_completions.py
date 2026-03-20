def test_chat_completions_requires_api_key(client):
    response = client.post(
        "/chat/completions",
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 401


def test_chat_completions_returns_non_stream_response(client, auth_headers):
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
    assert body["choices"][0]["message"]["content"] == "Echo: Hello"
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
