from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models import Stock, Index
from app.models.forex import ExchangeRate, ExchangeRateHistory
from app.db.session import get_db
from app.schemas.stock import StockSchema
from app.schemas.index import IndexSchema
from app.schemas.forex import ExchangeRateResponse
from app.services.search import search

router = APIRouter()


@router.get("/search", response_model=List[dict])
def search_items(
    query: str = Query(..., min_length=1),  # 최소 길이 1로 설정
    skip: int = Query(0, ge=0),  # 페이징을 위한 skip (0 이상)
    limit: int = Query(50, gt=0),  # 페이징을 위한 limit (0보다 큰 값)
    db: Session = Depends(get_db),  # DB 세션 의존성 주입
):

    results = search(db, query, skip, limit)

    return [{"model": result.__class__.__name__, "data": result} for result in results]
