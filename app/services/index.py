from sqlalchemy.orm import Session
from app.models.index import Index, IndexValue, index_component
from app.schemas.index import IndexSchema, IndexValueSchema, IndexGraphResponse, IndexGraphComponent
from typing import List

def create_index(db: Session, name: str, market_id: int, components: dict):
    idx = Index(name=name, market_id=market_id)
    db.add(idx)
    db.commit()
    db.refresh(idx)

    for stock_id, weight in components.items():
        db.execute(
            index_component.insert().values(index_id=idx.id, stock_id=stock_id, weight=weight)
        )
    db.commit()
    return idx


def update_index(db: Session, idx: Index, name: str, market_id: int, components: dict):
    idx.name = name
    idx.market_id = market_id
    db.commit()

    db.execute(index_component.delete().where(index_component.c.index_id == idx.id))
    for stock_id, weight in components.items():
        db.execute(
            index_component.insert().values(index_id=idx.id, stock_id=stock_id, weight=weight)
        )
    db.commit()
    db.refresh(idx)
    return idx


def get_index_detail(db: Session, index_id: int) -> IndexSchema:
    idx = db.query(Index).filter(Index.id == index_id).first()
    if not idx:
        raise ValueError("Index not found")

    comp_query = db.execute(
        "SELECT stock_id, weight FROM index_component WHERE index_id=:idx",
        {"idx": idx.id}
    ).fetchall()
    components = {c.stock_id: c.weight for c in comp_query}

    values = [
        IndexValueSchema(value=v.value, recorded_at=v.recorded_at)
        for v in idx.values
    ]

    return IndexSchema(
        id=idx.id,
        name=idx.name,
        market_id=idx.market_id,
        components=components,
        values=values,
    )


def get_index_graph(db: Session, index_id: int) -> IndexGraphResponse:
    idx = db.query(Index).filter(Index.id == index_id).first()
    if not idx:
        raise ValueError("Index not found")

    values_sorted = sorted(idx.values, key=lambda v: v.recorded_at)
    dates = [v.recorded_at.isoformat() for v in values_sorted]
    y_values = [v.value for v in values_sorted]

    comp_query = db.execute(
        "SELECT stock_id, weight FROM index_component WHERE index_id=:idx",
        {"idx": idx.id},
    ).fetchall()
    comp_weights = {c.stock_id: c.weight for c in comp_query}

    components: List[IndexGraphComponent] = [
        IndexGraphComponent(id=s.id, name=s.name, weight=comp_weights.get(s.id, 0.0))
        for s in idx.components
    ]

    return IndexGraphResponse(
        index_id=idx.id,
        index_name=idx.name,
        market_id=idx.market_id,
        graph={"dates": dates, "values": y_values},
        components=components,
    )
