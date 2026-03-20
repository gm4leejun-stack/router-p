import pytest

from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.services.chat_completion import ChatCompletionService


def test_chat_completion_request_accepts_openai_style_messages():
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hello"},
        ],
    )

    assert request.model == "qwen3:4b"
    assert request.stream is False
    assert request.messages[0].role == "system"


def test_chat_completion_request_requires_at_least_one_message():
    with pytest.raises(ValueError, match="at least one message"):
        ChatCompletionRequest(model="qwen3:4b", messages=[])


def test_service_returns_assistant_message_for_latest_user_prompt():
    service = ChatCompletionService()
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Summarize Phase 3"},
        ],
    )

    response = service.create_completion(request)

    assert response.object == "chat.completion"
    assert response.model == "qwen3:4b"
    assert response.choices[0].message.content == "Echo: Summarize Phase 3"
    assert response.choices[0].message.role == "assistant"


def test_service_rejects_requests_without_user_message():
    service = ChatCompletionService()
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[{"role": "system", "content": "Only instructions"}],
    )

    with pytest.raises(ValueError, match="at least one user message"):
        service.create_completion(request)
