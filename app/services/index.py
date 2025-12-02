from sqlalchemy.orm import Session
from app.models.index import Index, IndexValue, index_component
from app.schemas.index import (
    IndexSchema,
    IndexValueSchema,
    IndexGraphResponse,
    IndexGraphComponent,
)
from typing import List
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from app.models.index import Index, IndexValue
from datetime import datetime
import requests
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
    # Index 모델에서 해당 index_id에 대한 데이터 조회
    idx = db.query(Index).filter(Index.id == index_id).first()
    if not idx:
        raise ValueError("Index not found")

    # 기존 SQL 쿼리 텍스트를 text()로 감싸서 실행
    comp_query = db.execute(
        text("SELECT stock_id, weight FROM index_component WHERE index_id = :index_id"),
        {"index_id": idx.id},
    ).fetchall()

    # 쿼리 결과에서 stock_id와 weight를 dictionary 형태로 변환
    components = {c[0]: c[1] for c in comp_query}  # c[0]은 stock_id, c[1]은 weight

    # Index에 연결된 IndexValue ORM 관계를 통해 데이터 조회
    values = [
        IndexValueSchema(value=v.value, recorded_at=v.recorded_at) for v in idx.values
    ]

    # IndexSchema를 반환
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

def fetch_index_data_from_api(index_symbol: str):
    # API URL (예시: 인덱스 데이터 API)
    url = f"https://api.example.com/indices/{index_symbol}"

    # API 호출
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # API에서 받은 JSON 데이터를 반환
    else:
        return None  # 실패 시 None 반환


def save_index_data_to_db(db: Session, index_data: dict, index_symbol: str):
    # 인덱스 데이터 파싱
    index_name = index_data['name']
    index_value = index_data['value']

    # Index 테이블에 저장
    index = Index(
        name=index_name,
        symbol=index_symbol,
        market_id=1  # 예시로 1번 마켓 ID를 사용
    )
    db.add(index)
    db.commit()

    # IndexValue 테이블에 저장
    index_value_obj = IndexValue(
        index_id=index.id,
        value=index_value,
        recorded_at=datetime.utcnow()  # 현재 시간으로 기록
    )
    db.add(index_value_obj)
    db.commit()

    return index


def get_index_detail_from_api_and_save(db: Session, index_symbol: str):
    # API에서 데이터 가져오기
    index_data = fetch_index_data_from_api(index_symbol)

    if index_data is None:
        raise ValueError(f"Failed to fetch data for {index_symbol} from the API.")

    # DB에 저장
    index = save_index_data_to_db(db, index_data, index_symbol)

    # 저장된 데이터 반환
    return index
