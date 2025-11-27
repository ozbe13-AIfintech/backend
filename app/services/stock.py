from typing import List, Optional
from datetime import datetime
import os
import requests
from sqlalchemy.orm import Session
from app.models.stock import (
    Country,
    Market,
    Sector,
    Stock,
    StockPrice,
    StockPrediction,
    StockReview,
    SocialSentiment,
)


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


def get_stock_prices(db: Session, stock_id: int) -> List[StockPrice]:
    return (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at)
        .all()
    )


def get_stock_predictions(db: Session, stock_id: int) -> List[StockPrediction]:
    return db.query(StockPrediction).filter(StockPrediction.stock_id == stock_id).all()


def llm_predict(price_list: list):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    prompt = f"""
    너는 퀀트 기반의 금융 예측 전문가다.
    최근 30일의 주가(종가)는 다음과 같다:
    {price_list}

    위 데이터를 기반으로 다음 날 종가를 예측해줘.
    숫자만 출력해.
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


def get_stock_reviews(db: Session, stock_id: int) -> List[StockReview]:
    return db.query(StockReview).filter(StockReview.stock_id == stock_id).all()


def get_social_sentiments(db: Session, stock_id: int) -> List[SocialSentiment]:
    return db.query(SocialSentiment).filter(SocialSentiment.stock_id == stock_id).all()


def predict_stock(db: Session, stock_id: int):

    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at.desc())
        .limit(30)
        .all()
    )

    if not prices:
        return None

    price_list = [p.price for p in prices][::-1]

    prediction = llm_predict(price_list)

    if prediction is None:
        return None

    return {
        "prediction": float(prediction),
        "confidence": None,
        "model_name": "openai_gpt4",
        "created_at": datetime.utcnow(),
    }
