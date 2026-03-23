class FailingCloudProvider:
    def complete(self, request):
        raise RuntimeError("cloud failed")

    def stream_complete(self, request):
        raise RuntimeError("cloud failed")


def test_unauthorized_requests_return_stable_error_shape(client):
    response = client.get("/")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Unauthorized",
            "type": "auth_error",
        }
    }


def test_provider_failures_return_stable_error_shape(client, auth_headers, monkeypatch):
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


def test_streaming_provider_failures_before_first_chunk_return_stable_error_shape(
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
            "stream": True,
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
