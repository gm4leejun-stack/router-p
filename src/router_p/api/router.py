from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from router_p.api.dependencies import require_api_key
from router_p.api.streaming import format_sse_chunk, format_sse_done
from router_p.api.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from router_p.services.chat_completion import ChatCompletionService

router = APIRouter()


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
    request: Request,
    payload: ChatCompletionRequest,
) -> ChatCompletionResponse | StreamingResponse:
    service = ChatCompletionService(settings=request.app.state.settings)
    if payload.stream:
        chunk_id = "chatcmpl-stream"

        def event_stream():
            for chunk in service.stream_completion(payload):
                yield format_sse_chunk(chunk, chunk_id=chunk_id)
            yield format_sse_done()

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    return service.create_completion(payload)
