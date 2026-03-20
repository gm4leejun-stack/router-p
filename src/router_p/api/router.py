from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/", tags=["meta"])
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
