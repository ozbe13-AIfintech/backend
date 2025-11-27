from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

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
