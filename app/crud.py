from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    db_item = models.Item(title=item.title, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def list_items(db: Session, skip: int = 0, limit: int = 100) -> list[models.Item]:
    statement = select(models.Item).offset(skip).limit(limit).order_by(models.Item.id.desc())
    return list(db.scalars(statement).all())


def get_item(db: Session, item_id: int) -> models.Item | None:
    return db.get(models.Item, item_id)


def update_item(db: Session, item_id: int, item_update: schemas.ItemUpdate) -> models.Item | None:
    db_item = db.get(models.Item, item_id)
    if db_item is None:
        return None

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    db_item = db.get(models.Item, item_id)
    if db_item is None:
        return False

    db.delete(db_item)
    db.commit()
    return True


def create_uploaded_file(
    db: Session,
    *,
    original_filename: str,
    content_type: str | None,
    size_bytes: int,
    s3_bucket: str,
    s3_key: str,
) -> models.UploadedFile:
    db_file = models.UploadedFile(
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size_bytes,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def list_uploaded_files(db: Session, skip: int = 0, limit: int = 100) -> list[models.UploadedFile]:
    statement = select(models.UploadedFile).offset(skip).limit(limit).order_by(models.UploadedFile.id.desc())
    return list(db.scalars(statement).all())


def get_uploaded_file(db: Session, file_id: int) -> models.UploadedFile | None:
    return db.get(models.UploadedFile, file_id)
