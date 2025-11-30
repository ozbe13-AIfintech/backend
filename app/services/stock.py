from typing import List, Optional
from datetime import datetime
import os
from sqlalchemy import func
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException
import yfinance as yf
from app.models.stock import (
    Country, Market, Sector, Stock,
    StockPrice, StockPrediction, StockReview, SocialSentiment
)
from app.schemas.stock import StockReviewCreate,StockDetailResponse
from typing import Dict
import logging
from sqlalchemy.orm import aliased
def get_countries(db: Session) -> List[Country]:
    return db.query(Country).all()


def get_markets(db: Session, country_id: Optional[int] = None) -> List[Market]:
    query = db.query(Market)
    if country_id:
        query = query.filter(Market.country_id == country_id)
    return query.all()


def get_sectors(db: Session) -> List[Sector]:
    return db.query(Sector).all()


def get_stocks(db: Session, country_id=None, market_id=None, sector_id=None):
    query = db.query(
        Stock,
        Country.name.label("country"),
        Market.name.label("market"),
        Sector.name.label("sector")
    ).join(Country).join(Market, isouter=True).join(Sector, isouter=True)

    if country_id:
        query = query.filter(Stock.country_id == country_id)
    if market_id:
        query = query.filter(Stock.market_id == market_id)
    if sector_id:
        query = query.filter(Stock.sector_id == sector_id)

    results = []
    for stock, country, market, sector in query.all():
        latest_price = db.query(StockPrice).filter(StockPrice.stock_id == stock.id)\
                          .order_by(StockPrice.recorded_at.desc()).first()
        results.append(
            StockDetailResponse(
                id=stock.id,
                name=stock.name,
                symbol=stock.symbol,
                country=country,
                market=market,
                sector=sector,
                price=latest_price.price if latest_price else None,
                volume=latest_price.volume if latest_price else None,
                recorded_at=latest_price.recorded_at if latest_price else None,
            )
        )
    return results




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


def predict_stock(db: Session, stock_id: int, use_post: bool = False):
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


    if use_post:
        stock_pred = StockPrediction(
            stock_id=stock_id,
            predicted_price=prediction,
            model_name="openai_gpt4",
            created_at=datetime.utcnow()
        )
        db.add(stock_pred)
        db.commit()
        db.refresh(stock_pred)

    return {
        "prediction": float(prediction),
        "model_name": "openai_gpt4",
        "created_at": datetime.utcnow(),
    }


def get_top_gainers(db: Session, limit: int = 10):
    stocks = db.query(Stock).all()
    gainers = []

    for stock in stocks:
        prices = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.recorded_at.desc())
            .limit(2)
            .all()
        )
        if len(prices) < 2:
            continue

        latest = prices[0]
        previous = prices[1]

        if previous.price == 0:
            continue

        gain_percent = (latest.price - previous.price) / previous.price * 100
        gainers.append({
            "stock_id": stock.id,
            "name": stock.name,
            "gain_percent": gain_percent
        })


    top = sorted(gainers, key=lambda x: x["gain_percent"], reverse=True)[:limit]
    return top


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



def search_stocks(db: Session, query: str, skip: int = 0, limit: int = 50):
    return (
        db.query(Stock)
        .filter(
            (Stock.name.ilike(f"%{query}%")) | (Stock.ticker.ilike(f"%{query}%"))
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_or_create(session: Session, model, defaults=None, **kwargs):
    """SQLAlchemy에서 객체 조회 후 없으면 생성"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {**kwargs}
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance



logging.basicConfig(level=logging.DEBUG)




def insert_realtime_stock(session: Session, symbol: str) -> dict:
    symbol = symbol.upper()
    if not symbol:
        return {"symbol": symbol, "error": "Invalid symbol."}

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            raise ValueError(f"가격 데이터를 가져올 수 없습니다. symbol: {symbol}")

        row = hist.iloc[-1]
        price = float(row["Close"])
        open_price = float(row["Open"])
        high = float(row["High"])
        low = float(row["Low"])
        volume = int(row["Volume"])
        close_price = float(row["Close"])

        info = ticker.info
        stock_name = info.get("shortName", symbol)
        country_name = info.get("country") or "Unknown"
        market_name = info.get("exchange") or "Unknown"
        sector_name = info.get("sector") or "Unknown"

        # Country / Market / Sector 안전 조회 후 생성
        country = session.query(Country).filter_by(name=country_name).first()
        if not country:
            country = Country(name=country_name, code=country_name[:3])
            session.add(country)
            session.commit()
            session.refresh(country)

        market = session.query(Market).filter_by(name=market_name, country_id=country.id).first()
        if not market:
            market = Market(name=market_name, country_id=country.id)
            session.add(market)
            session.commit()
            session.refresh(market)

        sector = session.query(Sector).filter_by(name=sector_name).first()
        if not sector:
            sector = Sector(name=sector_name)
            session.add(sector)
            session.commit()
            session.refresh(sector)

        # Stock 조회 후 없으면 생성
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        if not stock:
            stock = Stock(
                symbol=symbol,
                name=stock_name,
                country_id=country.id,
                market_id=market.id,
                sector_id=sector.id
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)

        today = datetime.utcnow().date()

        exists = (
            session.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock.id,
                func.date(StockPrice.recorded_at) == today
            )
            .first()
        )
        if exists:
            return {
                "symbol": symbol,
                "name": stock_name,
                "price": price,
                "volume": volume,
                "saved": False,
                "message": "이미 오늘 데이터 존재"
            }


        stock_price = StockPrice(
            stock_id=stock.id,
            price=price,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=volume,
            recorded_at=datetime.utcnow()
        )
        session.add(stock_price)
        session.commit()
        session.refresh(stock_price)

        return {"symbol": symbol, "name": stock_name, "price": price, "volume": volume, "saved": True}

    except Exception as e:
        session.rollback()
        return {"symbol": symbol, "error": str(e)}



def insert_bulk_realtime_stocks(session: Session, symbols: List[str], update_threshold_minutes: int = 5) -> List[dict]:
    """여러 종목을 한 번에 실시간 갱신"""
    results = []
    for symbol in symbols:
        result = insert_realtime_stock(
            session=session,
            symbol=symbol,
            update_threshold_minutes=update_threshold_minutes
        )
        results.append(result)
    return results


# services/stock_service.py
def get_stocks_list(db: Session, country_id=None, market_id=None, sector_id=None):
    country_alias = aliased(Country)
    market_alias = aliased(Market)
    sector_alias = aliased(Sector)

    query = (
        db.query(
            Stock,
            country_alias.name.label("country"),
            market_alias.name.label("market"),
            sector_alias.name.label("sector"),
        )
        .select_from(Stock)
        .join(country_alias, Stock.country_id == country_alias.id)
        .outerjoin(market_alias, Stock.market_id == market_alias.id)
        .outerjoin(sector_alias, Stock.sector_id == sector_alias.id)
    )

    if country_id:
        query = query.filter(Stock.country_id == country_id)
    if market_id:
        query = query.filter(Stock.market_id == market_id)
    if sector_id:
        query = query.filter(Stock.sector_id == sector_id)

    results = []
    for stock, country_name, market_name, sector_name in query.all():
        latest_price = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.recorded_at.desc())
            .first()
        )
        results.append({
            "stock": stock,
            "country": country_name,
            "market": market_name,
            "sector": sector_name,
            "latest_price": latest_price
        })
    return results

def get_filtered_stocks(
    db: Session,
    country_id: Optional[int] = None,
    market_id: Optional[int] = None,
    sector_id: Optional[int] = None
) -> List[dict]:
    country_alias = aliased(Country)
    market_alias = aliased(Market)
    sector_alias = aliased(Sector)

    query = (
        db.query(
            Stock,
            country_alias.name.label("country"),
            market_alias.name.label("market"),
            sector_alias.name.label("sector"),
        )
        .select_from(Stock)
        .join(country_alias, Stock.country_id == country_alias.id)
        .outerjoin(market_alias, Stock.market_id == market_alias.id)
        .outerjoin(sector_alias, Stock.sector_id == sector_alias.id)
    )

    if country_id:
        query = query.filter(Stock.country_id == country_id)
    if market_id:
        query = query.filter(Stock.market_id == market_id)
    if sector_id:
        query = query.filter(Stock.sector_id == sector_id)

    results = []
    for stock, country_name, market_name, sector_name in query.all():
        latest_price = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.recorded_at.desc())
            .first()
        )
        results.append({
            "stock": stock,
            "country": country_name,
            "market": market_name,
            "sector": sector_name,
            "latest_price": latest_price
        })
    return results