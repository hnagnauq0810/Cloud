from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db import init_db
from app.routers import files, health, items


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI app deployed to AWS EC2 with RDS PostgreSQL, S3 storage, Docker and GitHub Actions.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "message": "Cloud FastAPI Deployment is running",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(health.router)
app.include_router(items.router)
app.include_router(files.router)
