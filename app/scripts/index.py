import yfinance as yf
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.index import Index, IndexValue
from app.services.index import calculate_change_percent

INDEX_SYMBOLS = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOWJONES": "^DJI",
    "RUSSELL2000": "^RUT",
    "FTSE100": "^FTSE",
    "DAX": "^GDAXI",
    "CAC40": "^FCHI",
    "NIKKEI225": "^N225",
    "HANGSENG": "^HSI",
    "SSE": "000001.SS",
    "SZI": "399001.SZ",
    "SENSEX": "^BSESN",
    "NIFTY50": "^NSEI",
    "TSX": "^GSPTSE",
}


def save_index_value(db: Session, index_obj: Index, value: float):
    iv = IndexValue(
        index_id=index_obj.id,
        value=value,
        recorded_at=datetime.utcnow()
    )
    db.add(iv)
    db.flush()


    calculate_change_percent(db, iv)


    index_obj.current_value = value
    index_obj.change = iv.change_percent

    return iv


def fetch_and_save(db: Session, name: str, symbol: str):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")

    if hist.empty:
        print(f"[WARN] {name}: 데이터 없음")
        return None

    close_price = float(hist["Close"].iloc[-1])


    index_obj = (
        db.query(Index).filter((Index.name == name) | (Index.symbol == symbol)).first()
    )

    if not index_obj:
        index_obj = Index(
            name=name,
            symbol=symbol,
            market_id=1,
            current_value=close_price,
        )
        db.add(index_obj)
        db.flush()


    save_index_value(db, index_obj, close_price)

    print(f"[INFO] {name} 저장됨: {close_price}")

    return index_obj


def main():
    db = SessionLocal()
    saved = []

    try:
        for name, symbol in INDEX_SYMBOLS.items():
            idx = fetch_and_save(db, name, symbol)
            if idx:
                saved.append(idx)

        db.commit()
        print(f"\n[SUCCESS] 총 {len(saved)}개 인덱스 저장 완료")

    except Exception as e:
        db.rollback()
        print("[ERROR]", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
