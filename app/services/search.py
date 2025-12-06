from sqlalchemy.orm import Session
from sqlalchemy import literal_column
from app.models import Stock, Index, ExchangeRate, ExchangeRateHistory


def search(db: Session, query: str, skip: int = 0, limit: int = 50):
    # Stock 테이블에서 name, symbol을 검색
    stock_query = db.query(
        Stock.name.label("name"),
        Stock.symbol.label("symbol"),
        literal_column("NULL").label(
            "base_currency"
        ),  # 다른 테이블에 없는 컬럼은 NULL로 채움
        literal_column("NULL").label("target_currency"),
        literal_column("NULL").label("rate"),
        literal_column("NULL").label("timestamp"),
        literal_column("NULL").label("last_updated"),
    ).filter(Stock.name.ilike(f"%{query}%") | Stock.symbol.ilike(f"%{query}%"))

    # Index 테이블에서 name, symbol을 검색
    index_query = db.query(
        literal_column("NULL").label("name"),
        literal_column("NULL").label("symbol"),
        literal_column("NULL").label("base_currency"),
        literal_column("NULL").label("target_currency"),
        literal_column("NULL").label("rate"),
        literal_column("NULL").label("timestamp"),
        literal_column("NULL").label("last_updated"),
    ).filter(Index.name.ilike(f"%{query}%") | Index.symbol.ilike(f"%{query}%"))

    # ExchangeRate 테이블에서 base_currency, target_currency 등을 검색
    exchange_rate_query = db.query(
        literal_column("NULL").label("name"),
        literal_column("NULL").label("symbol"),
        ExchangeRate.base_currency.label("base_currency"),
        ExchangeRate.target_currency.label("target_currency"),
        ExchangeRate.rate.label("rate"),
        literal_column("NULL").label("timestamp"),
        ExchangeRate.last_updated.label("last_updated"),
    ).filter(
        ExchangeRate.base_currency.ilike(f"%{query}%")
        | ExchangeRate.target_currency.ilike(f"%{query}%")
    )

    # ExchangeRateHistory 테이블에서 base_currency, target_currency 등을 검색
    exchange_rate_history_query = db.query(
        literal_column("NULL").label("name"),
        literal_column("NULL").label("symbol"),
        ExchangeRateHistory.base_currency.label("base_currency"),
        ExchangeRateHistory.target_currency.label("target_currency"),
        ExchangeRateHistory.rate.label("rate"),
        ExchangeRateHistory.timestamp.label("timestamp"),
        literal_column("NULL").label("last_updated"),
    ).filter(
        ExchangeRateHistory.base_currency.ilike(f"%{query}%")
        | ExchangeRateHistory.target_currency.ilike(f"%{query}%")
    )

    # 모든 쿼리 결과를 UNION ALL로 결합 (각 테이블에서 같은 컬럼 순서와 갯수로 맞춤)
    results = (
        stock_query.union_all(index_query)
        .union_all(exchange_rate_query)
        .union_all(exchange_rate_history_query)
    )

    # 페이징 처리
    return results.offset(skip).limit(limit).all()
