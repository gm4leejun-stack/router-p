from time import time
from uuid import uuid4

from router_p.api.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    ChatCompletionUsage,
)


class ChatCompletionService:
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

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid4().hex}",
            created=int(time()),
            model=request.model,
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
