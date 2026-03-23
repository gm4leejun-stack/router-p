from router_p.providers.types import ProviderChatResponse
from router_p.services.fallback_policy import FallbackPolicy


def test_fallback_policy_triggers_on_exception():
    policy = FallbackPolicy()

    assert policy.should_fallback_from_exception(RuntimeError("boom")) is True


def test_fallback_policy_triggers_on_timeout():
    policy = FallbackPolicy()

    assert policy.should_fallback_from_exception(TimeoutError("slow")) is True


def test_fallback_policy_triggers_on_short_output():
    policy = FallbackPolicy()
    response = ProviderChatResponse(
        content="short",
        prompt_tokens=30,
        completion_tokens=1,
        raw_model="qwen3:4b",
    )

    assert policy.should_fallback_from_response(response) is True


def test_fallback_policy_triggers_on_low_confidence_wording():
    policy = FallbackPolicy()
    response = ProviderChatResponse(
        content="I think maybe this could work",
        prompt_tokens=5,
        completion_tokens=6,
        raw_model="qwen3:4b",
    )

    assert policy.should_fallback_from_response(response) is True


def test_fallback_policy_accepts_healthy_response():
    policy = FallbackPolicy()
    response = ProviderChatResponse(
        content="Here is a concrete answer with enough detail",
        prompt_tokens=5,
        completion_tokens=8,
        raw_model="qwen3:4b",
    )

    assert policy.should_fallback_from_response(response) is False
