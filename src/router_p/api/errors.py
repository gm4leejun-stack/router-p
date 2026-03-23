from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    type: str


class ApiErrorEnvelope(BaseModel):
    error: ApiErrorDetail


class ApiError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str, error_type: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.error_type = error_type

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content=ApiErrorEnvelope(
                error=ApiErrorDetail(
                    code=self.code,
                    message=self.message,
                    type=self.error_type,
                )
            ).model_dump(),
        )


class AuthError(ApiError):
    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            message=message,
            error_type="auth_error",
        )


class ProviderError(ApiError):
    def __init__(self, message: str = "Provider request failed") -> None:
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="provider_error",
            message=message,
            error_type="provider_error",
        )


async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
    return exc.to_response()


async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return AuthError(str(exc.detail)).to_response()
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
