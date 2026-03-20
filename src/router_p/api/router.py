from fastapi import APIRouter, Depends, Request

from router_p.api.dependencies import require_api_key

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
