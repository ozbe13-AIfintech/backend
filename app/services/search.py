from sqlalchemy.orm import Session
from sqlalchemy import literal_column, String, Float, TIMESTAMP
from app.models import Stock, Index, ExchangeRate, ExchangeRateHistory


def search(db: Session, query: str, skip: int = 0, limit: int = 50):

    stock_query = db.query(
        Stock.name.label("name"),
        Stock.symbol.label("symbol"),
        literal_column("NULL").cast(String).label("base_currency"),
        literal_column("NULL").cast(String).label("target_currency"),
        literal_column("NULL").cast(Float).label("rate"),
        literal_column("NULL").cast(TIMESTAMP).label("timestamp"),
        literal_column("NULL").cast(TIMESTAMP).label("last_updated"),
    ).filter(Stock.name.ilike(f"%{query}%") | Stock.symbol.ilike(f"%{query}%"))


    index_query = db.query(
        literal_column("NULL").cast(String).label("name"),
        literal_column("NULL").cast(String).label("symbol"),
        literal_column("NULL").cast(String).label("base_currency"),
        literal_column("NULL").cast(String).label("target_currency"),
        literal_column("NULL").cast(Float).label("rate"),
        literal_column("NULL").cast(TIMESTAMP).label("timestamp"),
        literal_column("NULL").cast(TIMESTAMP).label("last_updated"),
    ).filter(Index.name.ilike(f"%{query}%") | Index.symbol.ilike(f"%{query}%"))


    exchange_rate_query = db.query(
        literal_column("NULL").cast(String).label("name"),
        literal_column("NULL").cast(String).label("symbol"),
        ExchangeRate.base_currency.label("base_currency"),
        ExchangeRate.target_currency.label("target_currency"),
        ExchangeRate.rate.label("rate"),
        literal_column("NULL").cast(TIMESTAMP).label("timestamp"),
        ExchangeRate.last_updated.label("last_updated"),
    ).filter(
        ExchangeRate.base_currency.ilike(f"%{query}%")
        | ExchangeRate.target_currency.ilike(f"%{query}%")
    )


    exchange_rate_history_query = db.query(
        literal_column("NULL").cast(String).label("name"),
        literal_column("NULL").cast(String).label("symbol"),
        ExchangeRateHistory.base_currency.label("base_currency"),
        ExchangeRateHistory.target_currency.label("target_currency"),
        ExchangeRateHistory.rate.label("rate"),
        ExchangeRateHistory.timestamp.label("timestamp"),
        literal_column("NULL").cast(TIMESTAMP).label("last_updated"),
    ).filter(
        ExchangeRateHistory.base_currency.ilike(f"%{query}%")
        | ExchangeRateHistory.target_currency.ilike(f"%{query}%")
    )


    results = (
        stock_query.union_all(index_query)
        .union_all(exchange_rate_query)
        .union_all(exchange_rate_history_query)
    )


    results_list = results.offset(skip).limit(limit).all()


    results_dicts = [dict(row._mapping) for row in results_list]

    return results_dicts

