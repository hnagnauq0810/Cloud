from fastapi import APIRouter

from app.core.config import get_settings
from app.db import check_db_connection
from app.services.s3_service import S3ConfigurationError, S3Service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "s3_configured": bool(settings.s3_bucket_name),
    }


@router.get("/db")
def database_health_check() -> dict:
    check_db_connection()
    return {"database": "ok"}


@router.get("/s3")
def s3_health_check() -> dict:
    try:
        ok = S3Service().check_bucket_access()
    except S3ConfigurationError:
        return {"s3": "not_configured"}
    return {"s3": "ok" if ok else "error"}
