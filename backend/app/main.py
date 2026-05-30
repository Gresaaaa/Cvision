import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.db.init_db import init_db
from app.middleware.request_context import RequestContextMiddleware

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    if settings.bootstrap_on_startup:
        init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["Meta"])
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "api_prefix": settings.api_v1_prefix,
    }


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}
