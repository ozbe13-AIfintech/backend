from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.schemas.forex import ExchangeRateResponse
from app.services.forex import get_exchange_rate, get_multiple_exchange_rates

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=ExchangeRateResponse)
def exchange_rate(
    base: str = Query("USD", min_length=3, max_length=3),
    target: str = Query("KRW", min_length=3, max_length=3),
    db: Session = Depends(get_db),
):
    return get_exchange_rate(base, target, db)

@router.get("/list", response_model=List[ExchangeRateResponse])
def list_exchange_rates(
    base: str = Query("USD", min_length=3, max_length=3),
    targets: str = Query("KRW,JPY,EUR,GBP,CNY,AUD,CAD,CHF,NZD,SGD"),
    db: Session = Depends(get_db),
):
    target_list = [t.strip() for t in targets.split(",")]
    return get_multiple_exchange_rates(base, target_list, db)
