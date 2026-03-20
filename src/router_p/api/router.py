from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"service": "router-p", "status": "booted"}
