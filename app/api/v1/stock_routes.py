from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.stock import Stock, StockReview
from app.models.user import User
from app.schemas.stock import (
    CountryResponse,
    MarketResponse,
    SectorResponse,
    StockResponse,
    StockReviewResponse,
    SocialSentimentResponse,
    StockSchema,
    StockReviewCreate,
)
from app.services import stock
from app.core.security import get_current_user

router = APIRouter()


@router.get("/countries", response_model=List[CountryResponse])
def list_countries(db: Session = Depends(get_db)):
    return stock.get_countries(db)


@router.get("/markets", response_model=List[MarketResponse])
def list_markets(country_id: Optional[int] = None, db: Session = Depends(get_db)):
    return stock.get_markets(db, country_id)


@router.get("/sectors", response_model=List[SectorResponse])
def list_sectors(db: Session = Depends(get_db)):
    return stock.get_sectors(db)


@router.get("/", response_model=List[StockResponse])
def list_stocks(
    country_id: Optional[int] = Query(None),
    market_id: Optional[int] = Query(None),
    sector_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    return stock.get_stocks(db, country_id, market_id, sector_id)


@router.get("/{stock_id}/graph")
def stock_graph_data(stock_id: int, db: Session = Depends(get_db)):

    prices = stock.get_stock_prices(db, stock_id)
    if not prices:
        raise HTTPException(status_code=404, detail="Stock prices not found")

    graph_data = {
        "dates": [p.recorded_at.isoformat() for p in prices],
        "prices": [p.price for p in prices],
        "open": [p.open for p in prices],
        "high": [p.high for p in prices],
        "low": [p.low for p in prices],
        "close": [p.close for p in prices],
        "volume": [p.volume for p in prices],
        "market_cap": [p.market_cap for p in prices],
        "market_index": [p.market_index for p in prices],
        "market_index_change": [p.market_index_change for p in prices],
    }

    return graph_data


@router.get("/{stock_id}/predict")
def stock_predict(stock_id: int, db: Session = Depends(get_db)):
    result = stock.predict_stock(db, stock_id)
    if not result:
        raise HTTPException(status_code=404, detail="Not enough data for prediction")
    return result


@router.get("/{stock_id}/reviews", response_model=List[StockReviewResponse])
def get_stock_reviews(stock_id: int, db: Session = Depends(get_db)):
    reviews = db.query(StockReview).filter(StockReview.stock_id == stock_id).all()
    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found")
    return reviews


@router.post("/{stock_id}/reviews", response_model=StockReviewResponse)
def create_stock_review(
    stock_id: int,
    data: StockReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock_obj = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock_obj:
        raise HTTPException(status_code=404, detail="Stock not found")

    review = StockReview(stock_id=stock_id, content=data.content, rating=data.rating)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{stock_id}/related_news", response_model=List[SocialSentimentResponse])
def related_news(stock_id: int, db: Session = Depends(get_db)):
    news = stock.get_social_sentiments(db, stock_id)
    if not news:
        raise HTTPException(status_code=404, detail="No related news found")
    return news


@router.get("/search", response_model=List[StockSchema])
def search_stocks(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    results = (
        db.query(stock)
        .filter((stock.name.ilike(f"%{query}%")) | (stock.ticker.ilike(f"%{query}%")))
        .all()
    )
    return results
