import os
import requests
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from collections import defaultdict
from dotenv import load_dotenv
from konlpy.tag import Okt
import re
from app.models.stock import SocialSentiment

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

okt = Okt()


POS_KO = ["좋다", "상승", "강세", "추천", "수익", "돌파", "성장", "가속화"]
NEG_KO = ["나쁘다", "하락", "약세", "손실", "위험", "감소", "둔화"]

POS_EN = ["good", "rise", "bullish", "profit", "increase", "gain", "surge", "growth"]
NEG_EN = ["bad", "fall", "bearish", "loss", "decline", "drop", "risk", "down"]


def analyze_sentiment(text: str) -> float:
    """
    한글 + 영어 뉴스 감정 분석
    점수 범위: -1 ~ 1
    """
    text_lower = text.lower()
    score = 0

    # 한글 분석
    for word in okt.morphs(text):
        if word in POS_KO:
            score += 1
        elif word in NEG_KO:
            score -= 1

    # 영어 분석
    words_en = re.findall(r"\b\w+\b", text_lower)
    for word in words_en:
        if word in POS_EN:
            score += 1
        elif word in NEG_EN:
            score -= 1

    # 정규화
    if score > 0:
        score = min(score / 5, 1)
    elif score < 0:
        score = max(score / 5, -1)

    return score


def fetch_news_for_stock(stock_name: str, language: str = "ko"):
    """
    뉴스 가져오기 (language: 'ko' 또는 'en')
    """
    url = f"https://newsapi.org/v2/everything?q={stock_name}&language={language}&apiKey={NEWS_API_KEY}"
    res = requests.get(url)

    if res.status_code != 200:
        raise HTTPException(500, "Failed to fetch news")

    articles = res.json().get("articles", [])
    # title + description 합쳐서 반환
    return [
        (a["title"] + " " + a.get("description", ""), "newsapi") for a in articles[:5]
    ]


def save_social_sentiment(db: Session, stock_id: int, content: str, source: str):
    score = analyze_sentiment(content)

    sentiment = SocialSentiment(
        stock_id=stock_id,
        content=content,
        source=source,
        sentiment_score=score,
        recorded_at=datetime.utcnow(),
    )

    db.add(sentiment)
    db.commit()
    db.refresh(sentiment)

    return sentiment


def fetch_and_save_sentiment_service(db: Session, stock_id: int, stock_name: str):
    articles = fetch_news_for_stock(stock_name)
    saved = []

    for content, source in articles:
        s = save_social_sentiment(db, stock_id, content, source)
        saved.append(
            {
                "id": s.id,
                "content": s.content,
                "source": s.source,
                "sentiment_score": s.sentiment_score,
            }
        )
    return saved


def sentiment_trend_service(db: Session, stock_id: int):
    sentiments = (
        db.query(SocialSentiment).filter(SocialSentiment.stock_id == stock_id).all()
    )

    if not sentiments:
        raise HTTPException(404, "No sentiment data found")

    daily_scores = defaultdict(list)

    for s in sentiments:
        date_str = s.recorded_at.date().isoformat()
        daily_scores[date_str].append(s.sentiment_score)

    dates = []
    avg_sentiment = []

    for date, scores in sorted(daily_scores.items()):
        dates.append(date)
        avg_sentiment.append(sum(scores) / len(scores))

    return {
        "stock_id": stock_id,
        "dates": dates,
        "avg_sentiment": avg_sentiment,
    }
