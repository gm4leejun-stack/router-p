from time import time
from uuid import uuid4

from router_p.api.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    ChatCompletionUsage,
)
from router_p.config import Settings, get_settings
from router_p.domain.model_slots import ModelSlot, is_cloud_slot, is_local_slot, resolve_model_slot
from router_p.providers.cloud import OpenAICompatibleCloudProvider
from router_p.providers.ollama import OllamaChatProvider
from router_p.providers.types import ProviderChatRequest
from router_p.services.rule_router import RuleRouter


class ChatCompletionService:
    def __init__(
        self,
        settings: Settings | None = None,
        router: RuleRouter | None = None,
        provider: OllamaChatProvider | None = None,
        cloud_provider: OpenAICompatibleCloudProvider | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._router = router or RuleRouter()
        self._provider = provider or OllamaChatProvider(base_url=self._settings.ollama_base_url)
        self._cloud_provider = cloud_provider or OpenAICompatibleCloudProvider(
            base_url=self._settings.cloud_base_url or "http://cloud.invalid",
            api_key=self._settings.cloud_api_key or "missing-cloud-api-key",
        )

    def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        for message in reversed(request.messages):
            if message.role == "user":
                last_user_message = message.content
                break
        else:
            raise ValueError("messages must contain at least one user message")

        content = f"Echo: {last_user_message}"
        prompt_tokens = sum(len(message.content.split()) for message in request.messages)
        completion_tokens = len(content.split())
        response_model = request.model
        target_slot: ModelSlot | None = None

        if request.model == "router-auto":
            decision = self._router.route(request)
            target_slot = decision.slot
            response_model = resolve_model_slot(decision.slot, self._settings) or decision.slot.value

        local_explicit_models = {
            self._settings.local_general_model,
            self._settings.local_code_model,
            self._settings.local_boundary_model,
        }
        cloud_explicit_models = {
            model
            for model in {
                self._settings.cloud_general_model,
                self._settings.cloud_code_model,
            }
            if model
        }

        should_use_local_provider = (
            target_slot is not None and is_local_slot(target_slot)
        ) or response_model in local_explicit_models
        should_use_cloud_provider = (
            target_slot is not None and is_cloud_slot(target_slot)
        ) or response_model in cloud_explicit_models

        if should_use_local_provider:
            provider_response = self._provider.complete(
                ProviderChatRequest(
                    model=response_model,
                    messages=request.messages,
                    timeout_seconds=self._settings.request_timeout_seconds,
                )
            )
            content = provider_response.content
            prompt_tokens = provider_response.prompt_tokens
            completion_tokens = provider_response.completion_tokens
            response_model = provider_response.raw_model
        elif should_use_cloud_provider:
            provider_response = self._cloud_provider.complete(
                ProviderChatRequest(
                    model=response_model,
                    messages=request.messages,
                    timeout_seconds=self._settings.request_timeout_seconds,
                )
            )
            content = provider_response.content
            prompt_tokens = provider_response.prompt_tokens
            completion_tokens = provider_response.completion_tokens
            response_model = provider_response.raw_model

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid4().hex}",
            created=int(time()),
            model=response_model,
            choices=[
                ChatCompletionChoice(
                    message=ChatCompletionResponseMessage(content=content),
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
