"""FastAPI application factory with lifespan initialization."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import build_cache
from app.core.config import settings
from app.data.database import Base, engine
from app.presentation.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize schema and cache backend on startup."""
    Base.metadata.create_all(bind=engine)
    app.state.cache = build_cache(settings.redis_url)
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    application = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    application.include_router(router)
    return application


app = create_app()
