from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from datetime import datetime
from typing import List
import requests
from sqlalchemy import text, bindparam

from sqlalchemy import select

import yfinance as yf
from app.models.index import Index, IndexValue, index_component
from app.schemas.index import (
    IndexSchema,
    IndexValueSchema,
    IndexGraphResponse,
    IndexGraphComponent,
)
from sqlalchemy.orm import Session, joinedload

YAHOO_INDEX_SYMBOLS = {
    "KOSPI": "^KS11",
    "NASDAQ": "^IXIC",
    "S&P500": "^GSPC",
    "DOWJONES": "^DJI",
    "FTSE100": "^FTSE",
    "NIKKEI225": "^N225",
    "HANGSENG": "^HSI",
    "DAX": "^GDAXI",
    "CAC40": "^FCHI",
}


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


def get_index_detail(db: Session, index_id: int) -> IndexSchema:
    idx = (
        db.query(Index)
        .options(joinedload(Index.values), joinedload(Index.components))
        .filter(Index.id == index_id)
        .first()
    )
    if not idx:
        raise ValueError("Index not found")

    comp_rows = db.execute(
"SELECT stock_id, weight FROM index_component WHERE index_id = :index_id",
{"index_id": idx.id},).fetchall()
    components = {row[0]: row[1] for row in comp_rows}

    values = [
        IndexValueSchema(
            value=v.value, recorded_at=v.recorded_at, change_percent=v.change_percent
        )
        for v in idx.values
    ]

    return IndexSchema(
        id=idx.id,
        name=idx.name,
        symbol=idx.symbol,
        market_id=idx.market_id,
        current_value=idx.current_value,
        change=idx.change,
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
        text("SELECT stock_id, weight FROM index_component WHERE index_id = :index_id"),
        {"index_id": idx.id},
    ).fetchall()

    comp_weights = {c[0]: c[1] for c in comp_query}

    components = [
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


def _get_previous_index_value(db: Session, index_value: IndexValue):
    previous_record = (
        db.query(IndexValue)
        .filter(IndexValue.index_id == index_value.index_id)
        .filter(IndexValue.recorded_at < index_value.recorded_at)
        .order_by(IndexValue.recorded_at.desc())
        .first()
    )

    return previous_record.value if previous_record else None


def save_index_value(db: Session, index_id: int, value: float):
    index_value = IndexValue(
        index_id=index_id, value=value, recorded_at=datetime.utcnow()
    )
    db.add(index_value)
    db.commit()
    db.refresh(index_value)


    calculate_change_percent(db, index_value)
    db.commit()

    return index_value


def calculate_change_percent(db: Session, index_value: IndexValue):
    previous_value = _get_previous_index_value(db, index_value)


    if previous_value and previous_value != 0:
        index_value.change_percent = (
            (index_value.value - previous_value) / previous_value * 100
        )
    else:
        index_value.change_percent = 0.0


def fetch_index_data_from_yahoo(symbol: str):
    """Yahoo Finance에서 인덱스 데이터 가져오기"""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")
    if hist.empty:
        print(f"[WARNING] {symbol} 데이터 없음")
        return None
    value = hist["Close"].iloc[-1]
    return float(value)


def save_multiple_indices_from_api(db: Session, symbols: dict = None):
    if symbols is None:
        symbols = YAHOO_INDEX_SYMBOLS

    saved_indices = []

    try:
        for name, yf_symbol in symbols.items():
            value = fetch_index_data_from_yahoo(yf_symbol)
            if value is None:
                print(f"[WARNING] {name} 데이터 가져오기 실패")
                continue


            idx = (
                db.query(Index)
                .filter((Index.symbol == yf_symbol) | (Index.name == name))
                .first()
            )
            if not idx:
                idx = Index(
                    name=name,
                    symbol=yf_symbol,
                    market_id=1,
                    current_value=value,
                    change=0.0,
                )
                db.add(idx)
                db.flush()
            else:
                idx.current_value = value
                idx.name = name


            index_value_obj = IndexValue(
                index_id=idx.id, value=value, recorded_at=datetime.utcnow()
            )
            db.add(index_value_obj)


            calculate_change_percent(db, index_value_obj)

            saved_indices.append(idx)


        db.commit()
        print(f"[INFO] {len(saved_indices)}개 인덱스 저장 완료")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 인덱스 저장 중 오류: {e}")
        raise

    return saved_indices


def list_indices_service(db) -> List[IndexSchema]:
    indices = db.query(Index).options(joinedload(Index.values)).all()
    if not indices:
        return []

    index_ids = [idx.id for idx in indices]


    comp_rows = db.execute(
        select(
            index_component.c.index_id,
            index_component.c.stock_id,
            index_component.c.weight,
        ).where(index_component.c.index_id.in_(index_ids))
    ).fetchall()

    comp_map = {}
    for row in comp_rows:
        idx_id, stock_id, weight = row
        comp_map.setdefault(idx_id, {})[stock_id] = weight

    result = []
    for idx in indices:
        values = [
            IndexValueSchema(
                value=v.value,
                recorded_at=v.recorded_at,
                change_percent=v.change_percent,
            )
            for v in idx.values
        ]
        idx_schema = IndexSchema(
            id=idx.id,
            name=idx.name,
            symbol=idx.symbol,
            market_id=idx.market_id,
            current_value=idx.current_value,
            change=idx.change,
            components=comp_map.get(idx.id, {}),
            values=values,
        )
        result.append(idx_schema)

    return result
