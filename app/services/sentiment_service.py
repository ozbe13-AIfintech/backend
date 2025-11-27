import os
import requests
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from collections import defaultdict
from dotenv import load_dotenv
from konlpy.tag import Okt

from app.models.stock import SocialSentiment

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

okt = Okt()



def analyze_sentiment_ko(text: str) -> float:
    pos_words = ["좋다", "상승", "강세", "추천", "수익"]
    neg_words = ["나쁘다", "하락", "약세", "손실", "위험"]

    score = 0
    for word in okt.morphs(text):
        if word in pos_words:
            score += 1
        elif word in neg_words:
            score -= 1

    # 점수 정규화
    if score > 0:
        score = min(score / 5, 1)
    elif score < 0:
        score = max(score / 5, -1)

    return score



def fetch_news_for_stock(stock_name: str):
    url = f"https://newsapi.org/v2/everything?q={stock_name}&language=ko&apiKey={NEWS_API_KEY}"
    res = requests.get(url)

    if res.status_code != 200:
        raise HTTPException(500, "Failed to fetch news")

    articles = res.json().get("articles", [])
    return [
        (a["title"] + " " + a.get("description", ""), "newsapi")
        for a in articles[:5]
    ]



def save_social_sentiment(db: Session, stock_id: int, content: str, source: str):
    score = analyze_sentiment_ko(content)

    sentiment = SocialSentiment(
        stock_id=stock_id,
        content=content,
        source=source,
        sentiment_score=score,
        recorded_at=datetime.utcnow()
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
    sentiments = db.query(SocialSentiment).filter(
        SocialSentiment.stock_id == stock_id
    ).all()

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
