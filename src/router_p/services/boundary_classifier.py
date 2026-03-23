from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.config import Settings, get_settings
from router_p.domain.model_slots import ModelSlot
from router_p.providers.ollama import OllamaChatProvider
from router_p.providers.types import ProviderChatRequest


class BoundaryClassifier:
    def __init__(
        self,
        settings: Settings | None = None,
        provider: OllamaChatProvider | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider or OllamaChatProvider(base_url=self._settings.ollama_base_url)

    def classify(self, request: ChatCompletionRequest) -> ModelSlot:
        response = self._provider.complete(
            ProviderChatRequest(
                model=self._settings.local_boundary_model,
                messages=request.messages,
                timeout_seconds=self._settings.request_timeout_seconds,
            )
        )
        normalized = response.content.strip().lower()
        mapping = {
            "local_text": ModelSlot.LOCAL_TEXT,
            "local_code": ModelSlot.LOCAL_CODE,
            "cloud_text": ModelSlot.CLOUD_TEXT,
            "cloud_code": ModelSlot.CLOUD_CODE,
        }
        return mapping.get(normalized, ModelSlot.LOCAL_TEXT)
