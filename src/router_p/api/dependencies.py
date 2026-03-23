from fastapi import Request

from router_p.api.errors import AuthError

def require_api_key(request: Request) -> None:
    expected = request.app.state.settings.api_key
    authorization = request.headers.get("Authorization")

    if authorization != f"Bearer {expected}":
        raise AuthError()
