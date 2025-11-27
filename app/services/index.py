from sqlalchemy.orm import Session
from app.models.index import Index, IndexValue, index_component


def create_index(db: Session, name: str, market_id: int, components: dict):
    idx = Index(name=name, market_id=market_id)
    db.add(idx)
    db.commit()
    db.refresh(idx)

    for stock_id, weight in components.items():
        db.execute(
            index_component.insert().values(
                index_id=idx.id, stock_id=stock_id, weight=weight
            )
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
            index_component.insert().values(
                index_id=idx.id, stock_id=stock_id, weight=weight
            )
        )
    db.commit()
    db.refresh(idx)
    return idx


def add_index_value(db: Session, index_id: int, value: float):
    val = IndexValue(index_id=index_id, value=value)
    db.add(val)
    db.commit()
    db.refresh(val)
    return val


def get_index_values(db: Session, index_id: int):
    return (
        db.query(IndexValue)
        .filter(IndexValue.index_id == index_id)
        .order_by(IndexValue.recorded_at.desc())
        .all()
    )
