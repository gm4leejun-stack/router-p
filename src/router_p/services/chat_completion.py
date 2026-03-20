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
from router_p.domain.model_slots import resolve_model_slot
from router_p.services.rule_router import RuleRouter


class ChatCompletionService:
    def __init__(
        self,
        settings: Settings | None = None,
        router: RuleRouter | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._router = router or RuleRouter()

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

        if request.model == "router-auto":
            decision = self._router.route(request)
            response_model = resolve_model_slot(decision.slot, self._settings) or decision.slot.value

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
