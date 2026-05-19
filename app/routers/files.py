from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import get_settings
from app.db import get_db
from app.services.s3_service import S3ConfigurationError, S3Service, S3UploadError

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=schemas.FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_to_s3(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        s3_service = S3Service()
    except S3ConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    try:
        result = s3_service.upload_bytes(
            content=content,
            filename=file.filename or "uploaded-file",
            content_type=file.content_type,
        )
    except S3UploadError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db_file = crud.create_uploaded_file(
        db,
        original_filename=file.filename or "uploaded-file",
        content_type=file.content_type,
        size_bytes=len(content),
        s3_bucket=result.bucket,
        s3_key=result.key,
    )

    return schemas.FileUploadResponse(
        id=db_file.id,
        original_filename=db_file.original_filename,
        size_bytes=db_file.size_bytes,
        s3_bucket=db_file.s3_bucket,
        s3_key=db_file.s3_key,
    )


@router.get("", response_model=list[schemas.FileRecordRead])
def list_files(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.list_uploaded_files(db, skip=skip, limit=limit)


@router.get("/{file_id}/presigned-url", response_model=schemas.PresignedUrlResponse)
def create_presigned_url(file_id: int, db: Session = Depends(get_db)):
    db_file = crud.get_uploaded_file(db, file_id)
    if db_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File record not found")

    try:
        url = S3Service().create_presigned_download_url(key=db_file.s3_key)
    except (S3ConfigurationError, S3UploadError) as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    settings = get_settings()
    return schemas.PresignedUrlResponse(
        file_id=db_file.id,
        expires_in_seconds=settings.presigned_url_expiration_seconds,
        url=url,
    )
