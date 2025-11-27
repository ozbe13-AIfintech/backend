from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.index import Index as IndexModel, IndexValue
from app.schemas.index import (
    IndexSchema,
    IndexCreate,
    IndexUpdate,
    IndexValueSchema,
    IndexGraphResponse,
    IndexGraphComponent,
)
from app.services import index as index_service
from typing import Dict, Any

router = APIRouter()


@router.get("/indices", response_model=List[IndexSchema])
def list_indices(db: Session = Depends(get_db)):
    indices = db.query(IndexModel).all()
    result = []
    for i in indices:

        comp_query = db.execute(
            "SELECT stock_id, weight FROM index_component WHERE index_id=:idx",
            {"idx": i.id},
        ).fetchall()
        components = {c.stock_id: c.weight for c in comp_query}
        result.append(
            IndexSchema(
                id=i.id,
                name=i.name,
                market_id=i.market_id,
                components=components,
                values=[],
            )
        )
    return result


@router.get("/indices/{index_id}", response_model=IndexSchema)
def get_index_detail(index_id: int, db: Session = Depends(get_db)):
    idx = db.query(IndexModel).filter(IndexModel.id == index_id).first()
    if not idx:
        raise HTTPException(status_code=404, detail="Index not found")

    comp_query = db.execute(
        "SELECT stock_id, weight FROM index_component WHERE index_id=:idx",
        {"idx": idx.id},
    ).fetchall()
    components = {c.stock_id: c.weight for c in comp_query}

    values = [
        IndexValueSchema(value=v.value, recorded_at=v.recorded_at) for v in idx.values
    ]

    return IndexSchema(
        id=idx.id,
        name=idx.name,
        market_id=idx.market_id,
        components=components,
        values=values,
    )


@router.post("/indices", response_model=IndexSchema)
def create_index_route(data: IndexCreate, db: Session = Depends(get_db)):
    idx = index_service.create_index(db, data.name, data.market_id, data.components)
    return get_index_detail(idx.id, db)


@router.put("/indices/{index_id}", response_model=IndexSchema)
def update_index_route(index_id: int, data: IndexUpdate, db: Session = Depends(get_db)):
    idx = db.query(IndexModel).filter(IndexModel.id == index_id).first()
    if not idx:
        raise HTTPException(status_code=404, detail="Index not found")
    idx = index_service.update_index(
        db, idx, data.name, data.market_id, data.components
    )
    return get_index_detail(idx.id, db)


@router.delete("/indices/{index_id}", response_model=dict)
def delete_index(index_id: int, db: Session = Depends(get_db)):
    idx = db.query(IndexModel).filter(IndexModel.id == index_id).first()
    if not idx:
        raise HTTPException(status_code=404, detail="Index not found")
    db.delete(idx)
    db.commit()
    return {"msg": "Index deleted successfully"}


@router.get("/indices/{index_id}/graph", response_model=IndexGraphResponse)
def get_index_graph(index_id: int, db: Session = Depends(get_db)):

    index = db.query(IndexModel).filter(IndexModel.id == index_id).first()
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")

    values = sorted(index.values, key=lambda v: v.recorded_at)
    dates: List[str] = [v.recorded_at.isoformat() for v in values]
    y_values: List[float] = [v.value for v in values]

    comp_query = db.execute(
        "SELECT stock_id, weight FROM index_component WHERE index_id=:idx",
        {"idx": index.id},
    ).fetchall()
    comp_weights = {c.stock_id: c.weight for c in comp_query}

    components: List[IndexGraphComponent] = [
        IndexGraphComponent(id=s.id, name=s.name, weight=comp_weights.get(s.id, 0.0))
        for s in index.components
    ]

    return IndexGraphResponse(
        index_id=index.id,
        index_name=index.name,
        market_id=index.market_id,
        graph={"dates": dates, "values": y_values},
        components=components,
    )
