import pytest

from router_p.api.schemas.chat import ChatCompletionRequest


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
