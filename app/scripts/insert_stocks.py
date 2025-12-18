
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


    info = ticker.info
    stock_name = info.get("shortName", symbol)
    country_name = info.get("country") or "Unknown"
    market_name = info.get("exchange") or "Unknown"
    sector_name = info.get("sector") or "Unknown"


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


    hist = ticker.history(period="1mo")
    if hist.empty:
        print(f"{symbol}: 가격 데이터 없음")
        return

    inserted_count = 0
    for date, row in hist.iterrows():
        recorded_at = (
            date.tz_convert("UTC").to_pydatetime()
            if hasattr(date, "tz_convert")
            else date.to_pydatetime()
        )
        recorded_date = recorded_at.date()


        exists = (
            db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock.id,
                func.date(StockPrice.recorded_at) == recorded_date,
            )
            .first()
        )
        if exists:
            continue

        stock_price = StockPrice(
            stock_id=stock.id,
            price=float(row["Close"]),
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            volume=int(row["Volume"]),
            recorded_at=recorded_at,
        )
        db.add(stock_price)
        inserted_count += 1

    db.commit()
    print(f"{symbol}: {inserted_count}개 가격 데이터 저장 완료")


if __name__ == "__main__":
    db = next(get_db())

    symbols = [

        "AAPL","MSFT","GOOG","GOOGL","AMZN","META","NVDA","TSLA",
        "ORCL","IBM","ADBE","INTC","AMD","QCOM","CSCO","NFLX",


        "CRWD","SNOW","PLTR","NET","MDB","DDOG",

        # 금융
        "JPM","BAC","WFC","C","GS","MS",

        # 산업/에너지
        "XOM","CVX","COP","SLB","CAT","GE","UNP",

        # 헬스케어
        "PFE","JNJ","UNH","MRK","ABBV",

        # 소비재
        "WMT","HD","COST","MCD","PG","KO","PEP","NKE",

        # 자동차
        "F","GM","RIVN","LCID",

        # ETF
        "SPY","QQQ","DIA","VTI","VOO","ARKK","XLK","XLF","XLE",

        # 한국 대형주
        "005930.KS","000660.KS","035420.KS","035720.KS",
        "005380.KS","051910.KS","068270.KS","207940.KS",
        "028260.KS","055550.KS","105560.KS",

        # 한국 ETF
        "069500.KS","122630.KS","233740.KS","251340.KS",

        # 글로벌 EV/배터리
        "NIO","LI","XPEV","BYDDF",
        "035900.KS","006400.KS",
    ]

    for s in symbols:
        insert_stock_price(db, s)

