from typing import List, Optional
from datetime import datetime
import os
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.stock import (
    Country, Market, Sector, Stock,
    StockPrice, StockPrediction, StockReview, SocialSentiment
)
from app.schemas.stock import StockReviewCreate


def get_countries(db: Session) -> List[Country]:
    return db.query(Country).all()


def get_markets(db: Session, country_id: Optional[int] = None) -> List[Market]:
    query = db.query(Market)
    if country_id:
        query = query.filter(Market.country_id == country_id)
    return query.all()


def get_sectors(db: Session) -> List[Sector]:
    return db.query(Sector).all()


def get_stocks(
    db: Session,
    country_id: Optional[int] = None,
    market_id: Optional[int] = None,
    sector_id: Optional[int] = None,
) -> List[Stock]:
    query = db.query(Stock)

    if country_id:
        query = query.filter(Stock.country_id == country_id)
    if market_id:
        query = query.filter(Stock.market_id == market_id)
    if sector_id:
        query = query.filter(Stock.sector_id == sector_id)

    return query.all()


def get_stock_graph(db: Session, stock_id: int):
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at)
        .all()
    )

    if not prices:
        raise HTTPException(404, "Stock prices not found")

    return {
        "dates": [p.recorded_at.isoformat() for p in prices],
        "prices": [p.price for p in prices],
        "open": [p.open for p in prices],
        "high": [p.high for p in prices],
        "low": [p.low for p in prices],
        "close": [p.close for p in prices],
        "volume": [p.volume for p in prices],
        "market_cap": [p.market_cap for p in prices],
        "market_index": [p.market_index for p in prices],
        "market_index_change": [p.market_index_change for p in prices],
    }


### =====================
###  예측 관련
### =====================
def llm_predict(price_list: list):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    prompt = f"""
    최근 30일의 종가 데이터:
    {price_list}
    다음 날 종가를 예측해 숫자만 출력.
    """

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    output = response.json()["choices"][0]["message"]["content"]

    try:
        return float(output.replace(",", "").replace("원", "").strip())
    except:
        return None


def predict_stock(db: Session, stock_id: int):
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at.desc())
        .limit(30)
        .all()
    )

    if not prices:
        raise HTTPException(404, "Not enough data for prediction")

    price_list = [p.price for p in prices][::-1]

    prediction = llm_predict(price_list)

    if prediction is None:
        raise HTTPException(500, "Prediction failed")

    return {
        "prediction": float(prediction),
        "confidence": None,
        "model_name": "openai_gpt4",
        "created_at": datetime.utcnow(),
    }


### =====================
###  리뷰
### =====================
def get_stock_reviews(db: Session, stock_id: int):
    return db.query(StockReview).filter(StockReview.stock_id == stock_id).all()


def create_review(db: Session, stock_id: int, data: StockReviewCreate, current_user):
    stock_obj = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock_obj:
        raise HTTPException(404, "Stock not found")

    review = StockReview(
        stock_id=stock_id,
        content=data.content,
        rating=data.rating,
        user_id=current_user.id
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    return review


### =====================
###  검색 기능
### =====================
def search_stocks(db: Session, query: str):
    return (
        db.query(Stock)
        .filter(
            (Stock.name.ilike(f"%{query}%"))
            | (Stock.ticker.ilike(f"%{query}%"))
        )
        .all()
    )
