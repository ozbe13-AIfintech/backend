# scripts/insert_stocks.py
import yfinance as yf
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.stock import Stock, StockPrice, Country, Market, Sector
import pytz

def insert_stock_price(db: Session, symbol: str):
    symbol = symbol.upper()
    ticker = yf.Ticker(symbol)

    # 종목 정보 가져오기
    info = ticker.info
    stock_name = info.get("shortName", symbol)
    country_name = info.get("country") or "Unknown"
    market_name = info.get("exchange") or "Unknown"
    sector_name = info.get("sector") or "Unknown"

    # Country/Market/Sector 조회 or 생성
    country = db.query(Country).filter_by(name=country_name).first()
    if not country:
        country = Country(name=country_name, code=country_name[:3])
        db.add(country)
        db.commit()
        db.refresh(country)

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

    # Stock 조회 or 생성
    stock = db.query(Stock).filter_by(symbol=symbol).first()
    if not stock:
        stock = Stock(
            symbol=symbol,
            name=stock_name,
            country_id=country.id,
            market_id=market.id,
            sector_id=sector.id
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

    # 최근 30일 가격 데이터 가져오기
    hist = ticker.history(period="1mo")
    if hist.empty:
        print(f"{symbol}: 가격 데이터 없음")
        return

    inserted_count = 0
    for date, row in hist.iterrows():
        # timezone 제거 + UTC로 통일
        recorded_at = date.tz_convert('UTC').to_pydatetime() if hasattr(date, 'tz_convert') else date.to_pydatetime()
        recorded_date = recorded_at.date()

        # 중복 체크 (같은 날 데이터 존재하면 삽입 X)
        exists = db.query(StockPrice).filter(
            StockPrice.stock_id == stock.id,
            func.date(StockPrice.recorded_at) == recorded_date
        ).first()
        if exists:
            continue

        stock_price = StockPrice(
            stock_id=stock.id,
            price=float(row['Close']),
            open=float(row['Open']),
            high=float(row['High']),
            low=float(row['Low']),
            close=float(row['Close']),
            volume=int(row['Volume']),
            recorded_at=recorded_at
        )
        db.add(stock_price)
        inserted_count += 1

    db.commit()
    print(f"{symbol}: {inserted_count}개 가격 데이터 저장 완료")


if __name__ == "__main__":
    db = next(get_db())
    symbols = ["AAPL", "MSFT", "GOOG", "TSLA", "AMZN"]
    for s in symbols:
        insert_stock_price(db, s)

