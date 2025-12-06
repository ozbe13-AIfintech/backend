# app/services/news.py
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.news import News
from app.models.stock import Stock
import requests
import os
from dotenv import load_dotenv
import re


load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_EVERYTHING_URL = "https://newsapi.org/v2/everything"

KST = timezone(timedelta(hours=9))


# -----------------------------------------
# 기사 포맷 변환
# -----------------------------------------
def _format_article(article: dict):
    published_str = article.get("publishedAt")

    if not published_str:
        published_at = datetime.now(KST)
    else:
        published_at = datetime.fromisoformat(
            published_str.replace("Z", "+00:00")
        ).astimezone(KST)

    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "source": article.get("source", {}).get("name"),
        "url": article.get("url"),
        "published_at": published_at,
    }


# -----------------------------------------
# 확장 심볼 키워드 (AI매칭 강화를 위해 추가)
# -----------------------------------------
extra_map = {
    "AAPL": ["apple", "apple inc", "애플", "아이폰", "팀 쿡", "애플 주가", "macbook", "iphone"],
    "TSLA": ["tesla", "테슬라", "일론 머스크", "elon musk", "전기차", "gigafactory"],
    "GOOGL": ["google", "구글", "알파벳", "검색엔진", "google ai"],
    "AMZN": ["amazon", "아마존", "aws", "프라임", "amazon cloud"],
}


# -----------------------------------------
# 확장 매칭 함수
# -----------------------------------------
def match_extra_symbol(text: str):
    text_lower = text.lower()

    for symbol, keywords in extra_map.items():
        for kw in keywords:
            kw_low = kw.lower()

            if kw_low in text_lower:
                return symbol

    return None


# -----------------------------------------
# 뉴스 Fetch + DB 저장
# -----------------------------------------
def fetch_and_save_news(db: Session, query: str = None, limit: int = 10, language: str = "ko"):
    url = NEWS_EVERYTHING_URL
    today = datetime.now(KST)
    from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

    default_query = "주식 OR 증시 OR 코스피 OR 코스닥 OR stock OR finance"
    search_query = query if query else default_query

    params = {
        "q": search_query,
        "language": language,
        "from": from_date,
        "pageSize": limit,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
    }

    # ------------------------------
    # API 요청
    # ------------------------------
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"뉴스 API 요청 실패: {e}")

    articles = res.json().get("articles", [])
    if not articles:
        print(f"{search_query} ({language}) 뉴스가 없습니다.")
        return []

    saved_news = []

    # ------------------------------
    # 기존 URL (중복 방지)
    # ------------------------------
    existing_urls = {
        row[0] for row in db.query(News.url).filter(News.url.isnot(None)).all()
    }

    # ------------------------------
    # stock 테이블 전체 조회
    # ------------------------------
    stocks = db.query(Stock).all()

    # -----------------------------------------
    # 주식명 + 심볼 매칭 함수
    # -----------------------------------------
    def match_stock(text: str):
        text_lower = text.lower()

        # 0) 확장 키워드 먼저 매칭
        extra_symbol = match_extra_symbol(text_lower)
        if extra_symbol:
            for s in stocks:
                if s.symbol.lower() == extra_symbol.lower():
                    return s.symbol, s.id

        # 1) stock DB 기반 매칭
        for s in stocks:
            symbol = s.symbol.lower()
            name = s.name.lower()

            name_variants = {
                name,
                name.replace(" ", ""),
                " ".join(list(name)),  # 삼성전자 → 삼 성 전 자
            }

            # 심볼 단어 매칭
            if re.search(rf"\b{re.escape(symbol)}\b", text_lower):
                return s.symbol, s.id

            # 이름 매칭
            for variant in name_variants:
                if variant and variant in text_lower:
                    return s.symbol, s.id

        return None, None

    # ------------------------------
    # 새 뉴스 저장
    # ------------------------------
    for article in articles:
        formatted = _format_article(article)

        title = formatted.get("title") or ""
        description = formatted.get("description") or ""
        url = formatted.get("url")

        if not url:
            print("URL 없는 뉴스 스킵:", title)
            continue

        if url in existing_urls:
            print("이미 DB에 있는 뉴스 스킵:", title)
            continue

        combined_text = (title + " " + description)

        # 주식 자동 매칭
        stock_symbol, stock_id = match_stock(combined_text)

        news_item = News(
            title=title,
            description=description,
            source=formatted.get("source"),
            url=url,
            published_at=formatted.get("published_at"),
            stock_symbol=stock_symbol,
            stock_id=stock_id,
        )

        db.add(news_item)
        saved_news.append(news_item)

    # ------------------------------
    # DB commit
    # ------------------------------
    if saved_news:
        try:
            db.commit()
            for n in saved_news:
                db.refresh(n)
            print(f"{len(saved_news)}개의 뉴스가 DB에 저장되었습니다.")
        except Exception as e:
            db.rollback()
            print("DB 저장 실패:", e)
            saved_news = []

    return saved_news


# -----------------------------------------
# 종목별 최근 뉴스 조회
# -----------------------------------------
def get_news_by_stock(db: Session, stock_symbol: str, limit: int = 10):
    stock = db.query(Stock).filter(Stock.symbol == stock_symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="주식 없음")

    return (
        db.query(News)
        .filter(News.stock_id == stock.id)
        .order_by(News.published_at.desc())
        .limit(limit)
        .all()
    )


# -----------------------------------------
# 최신 뉴스 조회
# -----------------------------------------
def get_latest_news(db: Session, limit: int = 10):
    return db.query(News).order_by(News.published_at.desc()).limit(limit).all()
