from fastapi import FastAPI, HTTPException

from router_p.api.errors import ApiError, handle_api_error, handle_http_exception
from router_p.api.router import router
from router_p.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
    )
    app.state.settings = app_settings
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.include_router(router)
    return app
