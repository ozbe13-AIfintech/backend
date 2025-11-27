import os
import requests
from sqlalchemy.orm import Session
from app.models.stock import SocialSentiment
from dotenv import load_dotenv
from konlpy.tag import Okt

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

    if score > 0:
        score = min(score / 5, 1)
    elif score < 0:
        score = max(score / 5, -1)
    return score


def save_social_sentiment(db: Session, stock_id: int, content: str, source: str):
    score = analyze_sentiment_ko(content)
    sentiment = SocialSentiment(
        stock_id=stock_id, content=content, source=source, sentiment_score=score
    )
    db.add(sentiment)
    db.commit()
    db.refresh(sentiment)
    return sentiment


def fetch_news_for_stock(stock_name: str):

    url = f"https://newsapi.org/v2/everything?q={stock_name}&language=ko&apiKey={NEWS_API_KEY}"
    res = requests.get(url)
    articles = res.json().get("articles", [])
    return [
        (a["title"] + " " + a.get("description", ""), "newsapi") for a in articles[:5]
    ]
