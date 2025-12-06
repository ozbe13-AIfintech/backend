# app/scripts/news.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.news import fetch_and_save_news
from app.models.stock import Stock

load_dotenv()

DB_URL = os.getenv("SYNC_DATABASE_URL")
if not DB_URL:
    raise ValueError("SYNC_DATABASE_URL 환경변수가 설정되지 않았습니다.")

engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine)


def main():
    print("뉴스 API 호출 및 DB 저장 시작...")

    with SessionLocal() as db:

        # ⭐ 모든 stock.symbol 가져오기
        symbols = [s.symbol for s in db.query(Stock).all()]
        print("검색할 종목:", symbols)

        total_saved = 0

        # ⭐ 각 종목마다 뉴스 가져오기
        for sym in symbols:
            print(f"\n--- {sym} 뉴스 가져오는 중... ---")
            news_list = fetch_and_save_news(
                db,
                query=sym,  # <-- 핵심!
                limit=20,
                language="en",  # 해외 기업은 영어 뉴스가 훨씬 많음
            )
            print(f"{sym}: {len(news_list)}개 저장됨")
            total_saved += len(news_list)

        print(f"\n총 {total_saved}개의 뉴스가 저장되었습니다.")


if __name__ == "__main__":
    main()
