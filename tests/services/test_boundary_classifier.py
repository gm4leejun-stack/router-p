from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.config import Settings
from router_p.domain.model_slots import ModelSlot
from router_p.providers.types import ProviderChatResponse
from router_p.services.boundary_classifier import BoundaryClassifier


class StubBoundaryProvider:
    def __init__(self, content: str) -> None:
        self._content = content
        self.last_model: str | None = None

    def complete(self, request):
        self.last_model = request.model
        return ProviderChatResponse(
            content=self._content,
            prompt_tokens=4,
            completion_tokens=1,
            raw_model=request.model,
        )


def test_boundary_classifier_uses_local_boundary_model():
    provider = StubBoundaryProvider("cloud_code")
    settings = Settings(local_boundary_model="phi4-mini")
    classifier = BoundaryClassifier(settings=settings, provider=provider)
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Need help deciding the best route"}],
    )

    classifier.classify(request)

    assert provider.last_model == "phi4-mini"


def test_boundary_classifier_normalizes_slot_output():
    provider = StubBoundaryProvider("cloud_code")
    classifier = BoundaryClassifier(settings=Settings(), provider=provider)
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Need help deciding the best route"}],
    )

    result = classifier.classify(request)

    assert result is ModelSlot.CLOUD_CODE


def test_boundary_classifier_falls_back_to_local_text_for_invalid_output():
    provider = StubBoundaryProvider("unknown")
    classifier = BoundaryClassifier(settings=Settings(), provider=provider)
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Need help deciding the best route"}],
    )

    result = classifier.classify(request)

    assert result is ModelSlot.LOCAL_TEXT
