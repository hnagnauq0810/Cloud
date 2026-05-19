from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db import get_db

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=schemas.ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@router.get("", response_model=list[schemas.ItemRead])
def list_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return crud.list_items(db, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=schemas.ItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return db_item


@router.patch("/{item_id}", response_model=schemas.ItemRead)
def update_item(item_id: int, item_update: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = crud.update_item(db, item_id, item_update)
    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return db_item


@router.delete("/{item_id}", response_model=schemas.Message)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return schemas.Message(message="Item deleted")
