from sqlalchemy.orm import Session
from datetime import datetime
import yfinance as yf
from app.models import Country, Market, Sector, Stock, StockPrice
from app.db.session import SessionLocal


def get_or_create(session: Session, model, defaults=None, **kwargs):
    """DB에 없으면 생성, 있으면 반환"""
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


def insert_realtime_stock(session: Session, symbol: str) -> dict:
    """yfinance에서 실시간 데이터 가져와 DB에 삽입"""
    symbol = symbol.upper()
    try:
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

        try:
            info = ticker.get_info()
        except:
            info = {}

        stock_name = info.get("shortName", symbol)
        country_name = info.get("country", "Unknown")
        market_name = info.get("exchange", "Unknown")
        sector_name = info.get("sector", "Unknown")

        # Country / Market / Sector
        country = get_or_create(
            session, Country, name=country_name, code=country_name[:3]
        )
        market = get_or_create(session, Market, name=market_name, country_id=country.id)
        sector = get_or_create(session, Sector, name=sector_name)

        # Stock 생성
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        if not stock:
            stock = Stock(
                symbol=symbol,
                name=stock_name,
                country_id=country.id,
                market_id=market.id,
                sector_id=sector.id,
                created_at=datetime.utcnow(),
            )
            session.add(stock)
            session.commit()
            session.refresh(stock)

        # StockPrice 생성
        stock_price = StockPrice(
            stock_id=stock.id,
            price=price,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=volume,
            recorded_at=datetime.now(),
        )
        session.add(stock_price)
        session.commit()
        session.refresh(stock_price)

        return {"symbol": symbol, "name": stock_name, "price": price, "saved": True}

    except Exception as e:
        session.rollback()
        return {"symbol": symbol, "error": str(e)}


def insert_bulk_stocks(session: Session, symbols: list):
    results = []
    for s in symbols:
        results.append(insert_realtime_stock(session, s))
    return results


def seed_extended_data(db: Session):
    """국가, 시장, 섹터 거의 실제 수준으로 세팅"""
    # Countries
    countries = [
        {"name": "United States", "code": "US"},
        {"name": "South Korea", "code": "KR"},
        {"name": "Japan", "code": "JP"},
        {"name": "China", "code": "CN"},
        {"name": "United Kingdom", "code": "UK"},
        {"name": "Germany", "code": "DE"},
        {"name": "India", "code": "IN"},
        {"name": "Australia", "code": "AU"},
        {"name": "Canada", "code": "CA"},
        {"name": "France", "code": "FR"},
        {"name": "Italy", "code": "IT"},
        {"name": "Brazil", "code": "BR"},
        {"name": "Mexico", "code": "MX"},
        {"name": "South Africa", "code": "ZA"},
        {"name": "Singapore", "code": "SG"},
        {"name": "Hong Kong", "code": "HK"},
        {"name": "Russia", "code": "RU"},
        {"name": "Taiwan", "code": "TW"},
        {"name": "Netherlands", "code": "NL"},
        {"name": "Switzerland", "code": "CH"},
    ]
    for c in countries:
        get_or_create(db, Country, **c)

    # Markets
    markets = [
        {"name": "NASDAQ", "country_name": "United States"},
        {"name": "NYSE", "country_name": "United States"},
        {"name": "AMEX", "country_name": "United States"},
        {"name": "KOSPI", "country_name": "South Korea"},
        {"name": "KOSDAQ", "country_name": "South Korea"},
        {"name": "JPX", "country_name": "Japan"},
        {"name": "Frankfurt Stock Exchange", "country_name": "Germany"},
        {"name": "BSE", "country_name": "India"},
        {"name": "Australian Securities Exchange", "country_name": "Australia"},
        {"name": "Toronto Stock Exchange", "country_name": "Canada"},
        {"name": "Euronext Paris", "country_name": "France"},
        {"name": "Milan Stock Exchange", "country_name": "Italy"},
        {"name": "BM&FBOVESPA", "country_name": "Brazil"},
        {"name": "Mexican Stock Exchange", "country_name": "Mexico"},
        {"name": "Singapore Exchange", "country_name": "Singapore"},
        {"name": "Hong Kong Stock Exchange", "country_name": "Hong Kong"},
        {"name": "Taiwan Stock Exchange", "country_name": "Taiwan"},
        {"name": "SIX Swiss Exchange", "country_name": "Switzerland"},
    ]
    for m in markets:
        country = db.query(Country).filter_by(name=m["country_name"]).first()
        if country:
            get_or_create(db, Market, name=m["name"], country_id=country.id)

    # Sectors
    sectors = [
        "Technology",
        "Consumer Cyclical",
        "Communication Services",
        "Financial Services",
        "Healthcare",
        "Industrials",
        "Energy",
        "Basic Materials",
        "Real Estate",
        "Utilities",
        "Consumer Defensive",
        "Materials",
        "Telecommunication Services",
        "Conglomerates",
    ]
    for s in sectors:
        get_or_create(db, Sector, name=s)

    print("✅ 시드 데이터 확장 완료")


if __name__ == "__main__":
    db = SessionLocal()
    seed_extended_data(db)

    # S&P500, NASDAQ 등 주요 심볼 수백 개 삽입 예시
    symbols = [
        "AAPL",
        "MSFT",
        "GOOG",
        "AMZN",
        "TSLA",
        "NFLX",
        "META",
        "NVDA",
        "SPY",
        "BABA",
        "KO",
        "JNJ",
        "V",
        "WMT",
        "DIS",
        "ORCL",
        "INTC",
        "CSCO",
        "PYPL",
        "ADBE",
        "T",
        "PFE",
        "XOM",
        "CVX",
        "BP",
        "RDS-A",
        "GM",
        "F",
        "BA",
        "MCD",
        "SBUX",
        "NKE",
        "HD",
        "LOW",
        "CAT",
        "DE",
        "GE",
        "IBM",
        "MRK",
        "ABT",
        # 필요하면 여기에 수백~수천 심볼 추가 가능
    ]

    results = insert_bulk_stocks(db, symbols)
    for r in results:
        print(r)

    db.close()
