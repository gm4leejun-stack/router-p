from pydantic import BaseModel, Field

from router_p.api.schemas.chat import ChatMessage


class ProviderChatRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[ChatMessage]
    timeout_seconds: float = Field(gt=0)


class ProviderChatResponse(BaseModel):
    content: str
    prompt_tokens: int
    completion_tokens: int
    raw_model: str
