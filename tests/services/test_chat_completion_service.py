import pytest

from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.config import Settings
from router_p.providers.types import ProviderChatResponse
from router_p.services.chat_completion import ChatCompletionService


class StubProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Provider hello",
            prompt_tokens=4,
            completion_tokens=2,
            raw_model=request.model,
        )


class StubCloudProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Cloud provider hello",
            prompt_tokens=6,
            completion_tokens=3,
            raw_model=request.model,
        )


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
    service = ChatCompletionService(provider=StubProvider())
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
    assert response.choices[0].message.content == "Provider hello"
    assert response.choices[0].message.role == "assistant"


def test_service_rejects_requests_without_user_message():
    service = ChatCompletionService()
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[{"role": "system", "content": "Only instructions"}],
    )

    with pytest.raises(ValueError, match="at least one user message"):
        service.create_completion(request)


def test_service_uses_route_decision_to_select_internal_model():
    settings = Settings(
        local_general_model="qwen3:4b",
        local_code_model="qwen2.5-coder:7b",
        cloud_general_model="gpt-general",
        cloud_code_model="gpt-code",
    )
    service = ChatCompletionService(settings=settings, provider=StubProvider())
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a Python unit test for a login handler"}],
    )

    response = service.create_completion(request)

    assert response.model == "qwen2.5-coder:7b"
    assert response.choices[0].message.content == "Provider hello"


def test_service_respects_explicit_model_without_rule_override():
    settings = Settings(local_general_model="qwen3:4b")
    service = ChatCompletionService(settings=settings, provider=StubProvider())
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[{"role": "user", "content": "Write a short greeting"}],
    )

    response = service.create_completion(request)

    assert response.model == "qwen3:4b"
    assert response.choices[0].message.content == "Provider hello"


def test_service_uses_cloud_provider_for_router_auto_complex_general_requests():
    settings = Settings(cloud_general_model="gpt-general")
    service = ChatCompletionService(
        settings=settings,
        provider=StubProvider(),
        cloud_provider=StubCloudProvider(),
    )
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Compare three architectures and migration strategy"}],
    )

    response = service.create_completion(request)

    assert response.model == "gpt-general"
    assert response.choices[0].message.content == "Cloud provider hello"


def test_service_uses_cloud_provider_for_router_auto_complex_code_requests():
    settings = Settings(cloud_code_model="gpt-code")
    service = ChatCompletionService(
        settings=settings,
        provider=StubProvider(),
        cloud_provider=StubCloudProvider(),
    )
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Multi-file codebase refactor and deep debugging plan"}],
    )

    response = service.create_completion(request)

    assert response.model == "gpt-code"
    assert response.choices[0].message.content == "Cloud provider hello"


def test_service_uses_cloud_provider_for_explicit_cloud_model():
    settings = Settings(cloud_general_model="gpt-general")
    service = ChatCompletionService(
        settings=settings,
        provider=StubProvider(),
        cloud_provider=StubCloudProvider(),
    )
    request = ChatCompletionRequest(
        model="gpt-general",
        messages=[{"role": "user", "content": "Hello cloud"}],
    )

    response = service.create_completion(request)

    assert response.model == "gpt-general"
    assert response.choices[0].message.content == "Cloud provider hello"
