from typing import List, Optional
from datetime import datetime
import os
from sqlalchemy import func
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException

#import yfinance as yf
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
from app.schemas.stock import (
    StockReviewCreate,
    StockDetailResponse,
    StockReviewResponse,
)
from typing import Dict
import logging
from sqlalchemy.orm import aliased
import pandas as pd
import numpy as np
from app.models.user import User
from sqlalchemy.orm import Session, joinedload


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
    query = (
        db.query(
            Stock,
            Country.name.label("country"),
            Market.name.label("market"),
            Sector.name.label("sector"),
        )
        .join(Country)
        .join(Market, isouter=True)
        .join(Sector, isouter=True)
    )

    if country_id:
        query = query.filter(Stock.country_id == country_id)
    if market_id:
        query = query.filter(Stock.market_id == market_id)
    if sector_id:
        query = query.filter(Stock.sector_id == sector_id)

    results = []
    for stock, country, market, sector in query.all():
        latest_price = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.recorded_at.desc())
            .first()
        )
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


def get_stock_graph(db: Session, stock_id: int, limit: int = 50):
    # DB에서 최근 limit개 데이터 가져오기
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at.desc())
        .limit(limit)
        .all()
    )

    if not prices:
        raise HTTPException(status_code=404, detail="Stock prices not found")

    # 오래된 → 최신 순으로 정렬
    prices.reverse()

    # Pandas DataFrame으로 변환
    df = pd.DataFrame(
        [
            {
                "date": p.recorded_at,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
                "market_cap": p.market_cap,
                "market_index": p.market_index,
                "market_index_change": p.market_index_change,
            }
            for p in prices
        ]
    )

    # 이동평균 계산
    df["ma5"] = df["close"].rolling(window=5).mean()
    df["ma10"] = df["close"].rolling(window=10).mean()

    # ApexCharts용 시리즈 생성
    candle_series = [
        {"x": row.date.isoformat(), "y": [row.open, row.high, row.low, row.close]}
        for row in df.itertuples()
    ]
    volume_series = [
        {"x": row.date.isoformat(), "y": row.volume} for row in df.itertuples()
    ]
    ma5_series = [
        {"x": row.date.isoformat(), "y": row.ma5 if not pd.isna(row.ma5) else None}
        for row in df.itertuples()
    ]
    ma10_series = [
        {"x": row.date.isoformat(), "y": row.ma10 if not pd.isna(row.ma10) else None}
        for row in df.itertuples()
    ]

    return {
        "candle": candle_series,
        "volume": volume_series,
        "ma5": ma5_series,
        "ma10": ma10_series,
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

    # 응답 구조 로깅
    logging.debug("API Response: %s", response.json())

    # 응답에서 'choices'가 있는지 확인
    response_json = response.json()

    if "choices" not in response_json:
        logging.error("API Response does not contain 'choices': %s", response_json)
        return None  # 'choices'가 없으면 None을 반환하거나 예외를 처리

    # 정상적으로 'choices' 키가 있다면
    output = response_json["choices"][0]["message"]["content"]
    try:
        return float(output.replace(",", "").replace("원", "").strip())
    except:
        logging.error("Error while parsing prediction output: %s", output)
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
            created_at=datetime.utcnow(),
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
        gainers.append(
            {"stock_id": stock.id, "name": stock.name, "gain_percent": gain_percent}
        )

    top = sorted(gainers, key=lambda x: x["gain_percent"], reverse=True)[:limit]
    return top


def get_stock_reviews(db: Session, stock_id: int) -> list[StockReviewResponse]:
    """
    특정 주식 리뷰 조회 (최신순)
    로그인 필요 없음
    """
    reviews = (
        db.query(StockReview)
        .options(joinedload(StockReview.user))  # user 객체 미리 로딩
        .filter(StockReview.stock_id == stock_id)
        .order_by(StockReview.created_at.desc())
        .all()
    )

    # user가 없는 경우는 제외
    return [
        StockReviewResponse(
            id=r.id,
            content=r.content,
            rating=r.rating,
            created_at=r.created_at,
            user_id=r.user.id,
            user_name=r.user.nickname,
        )
        for r in reviews
        if r.user
    ]


def create_stock_review(
    db: Session, stock_id: int, data: StockReviewCreate, current_user: User
) -> StockReviewResponse:
    """
    리뷰 작성 (로그인 필요)
    """
    stock_obj = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock_obj:
        raise HTTPException(status_code=404, detail="Stock not found")

    review = StockReview(
        stock_id=stock_id,
        content=data.content,
        rating=data.rating,
        user_id=current_user.id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return StockReviewResponse(
        id=review.id,
        content=review.content,
        rating=review.rating,
        created_at=review.created_at,
        user_id=current_user.id,
        user_name=current_user.nickname,
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


def to_native(x):
    """numpy 타입을 기본 Python 타입으로 변환"""
    if isinstance(x, (np.float32, np.float64)):
        return float(x)
    elif isinstance(x, (np.int32, np.int64, np.uint32, np.uint64)):
        return int(x)
    elif isinstance(x, np.generic):  # 나머지 numpy 스칼라
        return x.item()
    return x


def insert_stock_price(db: Session, symbol: str):
    symbol = symbol.upper()
    #ticker = yf.Ticker(symbol)

    # 종목 정보 가져오기
    #info = ticker.info
    stock_name = info.get("shortName", symbol)
    country_name = info.get("country") or "Unknown"
    market_name = info.get("exchange") or "Unknown"
    sector_name = info.get("sector") or "Unknown"

    # Country 조회/생성
    country = db.query(Country).filter_by(name=country_name).first()
    if not country:
        country = Country(name=country_name, code=country_name[:3])
        db.add(country)
        db.commit()
        db.refresh(country)

    # Market 조회/생성
    market = db.query(Market).filter_by(name=market_name, country_id=country.id).first()
    if not market:
        market = Market(name=market_name, country_id=country.id)
        db.add(market)
        db.commit()
        db.refresh(market)

    sector = db.query(Sector).filter_by(name=sector_name).first()
    if not sector:
        sector = Sector(name=sector_name)
        db.add(sector)
        db.commit()
        db.refresh(sector)

    # Stock 조회/생성
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        stock = Stock(
            symbol=symbol,
            name=stock_name,
            country_id=country.id,
            market_id=market.id,
            sector_id=sector.id,
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

    # 최근 30일 가격 데이터 가져오기
    hist = ticker.history(period="1mo")
    if hist.empty:
        print(f"{symbol}: 가격 데이터 없음")
        return

    for date, row in hist.iterrows():
        exists = (
            db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock.id,
                StockPrice.recorded_at == date.to_pydatetime(),
            )
            .first()
        )
        if exists:
            continue

        # numpy 타입 → float/int 변환
        stock_price = StockPrice(
            stock_id=stock.id,
            price=float(row["Close"]),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]),
            recorded_at=date.to_pydatetime(),
        )
        db.add(stock_price)
    db.commit()
    print(f"{symbol}: {len(hist)}개 가격 데이터 저장 완료")


logging.basicConfig(level=logging.DEBUG)


def insert_realtime_stock(session: Session, symbol: str) -> dict:
    symbol = symbol.upper()
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return {"symbol": symbol, "error": "데이터 없음"}

        row = hist.iloc[-1]

        # numpy → float/int 변환
        price = float(row["Close"])
        open_price = float(row["Open"])
        high = float(row["High"])
        low = float(row["Low"])
        close_price = float(row["Close"])
        volume = int(row["Volume"])

        info = ticker.info
        stock_name = info.get("shortName", symbol)
        country_name = info.get("country") or "Unknown"
        market_name = info.get("exchange") or "Unknown"
        sector_name = info.get("sector") or "Unknown"

        # Country / Market / Sector 조회/생성
        country = session.query(Country).filter_by(name=country_name).first()
        if not country:
            country = Country(name=country_name, code=country_name[:3])
            session.add(country)
            session.commit()
            session.refresh(country)

        market = (
            session.query(Market)
            .filter_by(name=market_name, country_id=country.id)
            .first()
        )
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

        # Stock 조회/생성
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        if not stock:
            stock = Stock(
                symbol=symbol,
                name=stock_name,
                country_id=country.id,
                market_id=market.id,
                sector_id=sector.id,
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)

        today = datetime.utcnow().date()

        exists = (
            session.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock.id,
                func.date(StockPrice.recorded_at) == today,
            )
            .first()
        )
        if exists:
            return {
                "symbol": symbol,
                "saved": False,
                "message": "이미 오늘 데이터 존재",
            }

        stock_price = StockPrice(
            stock_id=stock.id,
            price=price,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=volume,
            recorded_at=datetime.utcnow(),
        )
        session.add(stock_price)
        session.commit()
        session.refresh(stock_price)

        return {"symbol": symbol, "saved": True, "price": price, "volume": volume}

    except Exception as e:
        session.rollback()
        return {"symbol": symbol, "error": str(e)}


def insert_bulk_realtime_stocks(session: Session, symbols: List[str]) -> List[dict]:
    """여러 종목을 한 번에 실시간 갱신"""
    results = []
    for symbol in symbols:
        try:
            # 여기에서 float으로 변환하는 부분을 명확하게 추가할 수 있습니다.
            result = insert_realtime_stock(session=session, symbol=symbol)
            results.append(result)
        except Exception as e:
            # 개별 심볼 오류는 기록하고 계속 진행
            results.append({"symbol": symbol, "error": str(e)})
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
        results.append(
            {
                "stock": stock,
                "country": country_name,
                "market": market_name,
                "sector": sector_name,
                "latest_price": latest_price,
            }
        )
    return results


def get_filtered_stocks(
    db: Session,
    country_id: Optional[int] = None,
    market_id: Optional[int] = None,
    sector_id: Optional[int] = None,
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
        results.append(
            {
                "stock": stock,
                "country": country_name,
                "market": market_name,
                "sector": sector_name,
                "latest_price": latest_price,
            }
        )
    return results


def get_stock_by_id(db: Session, stock_id: int) -> Optional[dict]:
    """
    특정 stock_id의 주식 상세 정보 조회
    """
    country_alias = aliased(Country)
    market_alias = aliased(Market)
    sector_alias = aliased(Sector)

    # 주식과 관련 정보 조회
    item = (
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
        .filter(Stock.id == stock_id)
        .first()
    )

    if not item:
        return None

    stock, country_name, market_name, sector_name = item

    latest_price = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock.id)
        .order_by(StockPrice.recorded_at.desc())
        .first()
    )

    return {
        "stock": stock,
        "country": country_name,
        "market": market_name,
        "sector": sector_name,
        "latest_price": latest_price,
    }
def delete_stock_review(db: Session, review_id: int, current_user: User):
    review = db.query(StockReview).filter(StockReview.id == review_id).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # 본인 리뷰인지 체크
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this review")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted"}
