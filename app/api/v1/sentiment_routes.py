from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.sentiment_service import (
    fetch_and_save_sentiment_service,
    sentiment_trend_service
)

router = APIRouter()


@router.post("/fetch/{stock_id}")
def fetch_and_save_sentiment(stock_id: int, stock_name: str, db: Session = Depends(get_db)):
    return fetch_and_save_sentiment_service(db, stock_id, stock_name)


@router.get("/analytics/{stock_id}")
def sentiment_trend(stock_id: int, db: Session = Depends(get_db)):
    return sentiment_trend_service(db, stock_id)

