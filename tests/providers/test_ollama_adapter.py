from router_p.api.schemas.chat import ChatMessage
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
