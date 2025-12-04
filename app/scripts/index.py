from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services import index as index_service

# 가져올 인덱스 심볼 지정 (원하는 만큼)
INDEX_SYMBOLS = {
    "KOSPI": "^KS11",
    "NASDAQ": "^IXIC",
    "S&P500": "^GSPC",
    "DOWJONES": "^DJI",
    "FTSE100": "^FTSE",
    "NIKKEI225": "^N225",
    "HANGSENG": "^HSI",
    "DAX": "^GDAXI",
    "CAC40": "^FCHI"
}

def main():
    db: Session = SessionLocal()
    try:
        saved_indices = index_service.save_multiple_indices_from_api(db, INDEX_SYMBOLS)
        print(f"[INFO] {len(saved_indices)}개 인덱스 저장 완료")
        for idx in saved_indices:
            print(f"  - {idx.name} ({idx.symbol}) 저장 완료")
    finally:
        db.close()

if __name__ == "__main__":
    main()
