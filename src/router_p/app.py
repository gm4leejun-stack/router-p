from fastapi import FastAPI

from router_p.api.router import router
from router_p.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
    )
    app.state.settings = app_settings
    app.include_router(router)
    return app
