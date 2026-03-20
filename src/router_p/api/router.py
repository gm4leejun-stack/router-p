from fastapi import APIRouter, Depends, HTTPException, Request, status

from router_p.api.dependencies import require_api_key
from router_p.api.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from router_p.services.chat_completion import ChatCompletionService

router = APIRouter()
chat_completion_service = ChatCompletionService()


@router.get("/", tags=["meta"], dependencies=[Depends(require_api_key)])
async def root() -> dict[str, str]:
    return {"service": "router-p", "status": "booted"}


@router.get("/health", tags=["meta"])
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "service": "router-p",
        "status": "ready",
        "environment": settings.environment,
    }


@router.post(
    "/chat/completions",
    tags=["chat"],
    dependencies=[Depends(require_api_key)],
    response_model=ChatCompletionResponse,
)
async def create_chat_completion(
    payload: ChatCompletionRequest,
) -> ChatCompletionResponse:
    if payload.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is not supported yet",
        )
    return chat_completion_service.create_completion(payload)
