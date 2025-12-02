from fastapi import APIRouter, Query, Depends
from app.services.forex import get_exchange_rate
from app.schemas.forex import ExchangeRateResponse
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
router = APIRouter()

def get_db():
    db = SessionLocal()  # 세션 생성
    try:
        yield db  # 세션을 반환
    finally:
        db.close()  # 세션 닫기

@router.get("/", response_model=ExchangeRateResponse)
def exchange_rate(
    base: str = Query("USD", min_length=3, max_length=3),
    target: str = Query("KRW", min_length=3, max_length=3),
    db: Session = Depends(get_db),  # DB 세션을 의존성으로 받기
):
    return get_exchange_rate(base, target, db)
