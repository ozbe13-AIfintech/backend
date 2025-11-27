from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.stock import SocialSentiment
from app.schemas.stock import (SocialSentimentResponse)

from app.db.session import get_db
from app.services.sentiment_service import fetch_news_for_stock, save_social_sentiment

router = APIRouter()


@router.post("/fetch/{stock_id}")
def fetch_and_save_sentiment(
    stock_id: int, stock_name: str, db: Session = Depends(get_db)
):

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

@router.get("/analytics/{stock_id}")
def sentiment_trend(stock_id: int, db: Session = Depends(get_db)):
    sentiments = db.query(SocialSentiment).filter(SocialSentiment.stock_id==stock_id).all()
    if not sentiments:
        raise HTTPException(status_code=404, detail="No sentiment data found")


    from collections import defaultdict
    daily_scores = defaultdict(list)
    for s in sentiments:
        date_str = s.recorded_at.date().isoformat()
        daily_scores[date_str].append(s.sentiment_score)

    dates = []
    avg_sentiment = []
    for date, scores in sorted(daily_scores.items()):
        dates.append(date)
        avg_sentiment.append(sum(scores)/len(scores))

    return {"stock_id": stock_id, "dates": dates, "avg_sentiment": avg_sentiment}


