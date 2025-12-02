from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.index import IndexSchema, IndexCreate, IndexUpdate, IndexGraphResponse
from app.services import index as index_service

router = APIRouter()


@router.get("/indices", response_model=List[IndexSchema])
def list_indices(db: Session = Depends(get_db)):
    indices = db.query(index_service.Index).all()
    return [index_service.get_index_detail(db, i.id) for i in indices]


@router.get("/indices/{index_id}", response_model=IndexSchema)
def get_index_detail(index_id: int, db: Session = Depends(get_db)):
    try:
        return index_service.get_index_detail(db, index_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/indices", response_model=IndexSchema)
def create_index_route(data: IndexCreate, db: Session = Depends(get_db)):
    idx = index_service.create_index(db, data.name, data.market_id, data.components)
    return index_service.get_index_detail(db, idx.id)


@router.put("/indices/{index_id}", response_model=IndexSchema)
def update_index_route(index_id: int, data: IndexUpdate, db: Session = Depends(get_db)):
    idx_obj = (
        db.query(index_service.Index).filter(index_service.Index.id == index_id).first()
    )
    if not idx_obj:
        raise HTTPException(status_code=404, detail="Index not found")
    idx = index_service.update_index(
        db, idx_obj, data.name, data.market_id, data.components
    )
    return index_service.get_index_detail(db, idx.id)


@router.delete("/indices/{index_id}", response_model=dict)
def delete_index(index_id: int, db: Session = Depends(get_db)):
    idx = (
        db.query(index_service.Index).filter(index_service.Index.id == index_id).first()
    )
    if not idx:
        raise HTTPException(status_code=404, detail="Index not found")
    db.delete(idx)
    db.commit()
    return {"msg": "Index deleted successfully"}


@router.get("/indices/{index_id}/graph", response_model=IndexGraphResponse)
def get_index_graph(index_id: int, db: Session = Depends(get_db)):
    try:
        return index_service.get_index_graph(db, index_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
