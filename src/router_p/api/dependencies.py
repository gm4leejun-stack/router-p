from fastapi import HTTPException, Request, status


def require_api_key(request: Request) -> None:
    expected = request.app.state.settings.api_key
    authorization = request.headers.get("Authorization")

    if authorization != f"Bearer {expected}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
