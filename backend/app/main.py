from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, dashboard, detections, heatmap, inventory, notifications, recommendations
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.init_db import create_database, seed_default_users
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_database()
    db = SessionLocal()
    try:
        seed_default_users(db)
    finally:
        db.close()
    yield


def create_app(init_database: bool = True) -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.API_VERSION,
        lifespan=lifespan if init_database else None,
    )
    cors_origins = [
        origin.strip()
        for origin in settings.FRONTEND_CORS_ORIGINS.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(auth.router)
    app.include_router(detections.router)
    app.include_router(recommendations.router)
    app.include_router(inventory.router)
    app.include_router(notifications.router)
    app.include_router(dashboard.router)
    app.include_router(heatmap.router)
    return app


app = create_app()
