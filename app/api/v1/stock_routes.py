from fastapi import APIRouter, Depends,Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stock import (
    CountryResponse,
    MarketResponse,
    SectorResponse,
    StockResponse,
    StockReviewResponse,
    StockSchema,
    StockReviewCreate,
    StockPriceResponse,
    StockPredictionResponse
)
from app.services import stock
from app.core.security import get_current_user
from app.models.user import User

from typing import Optional, List
from datetime import datetime

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




@router.get("/{stock_id}/graph", response_model=List[StockPriceResponse])
def stock_graph_data(stock_id: int, db: Session = Depends(get_db)):
    data = stock.get_stock_graph(db, stock_id)
    return [
        StockPriceResponse(
            price=data["prices"][i],
            open=data["open"][i],
            high=data["high"][i],
            low=data["low"][i],
            close=data["close"][i],
            volume=data["volume"][i],
            market_cap=data["market_cap"][i],
            market_index=data["market_index"][i],
            market_index_change=data["market_index_change"][i],
            recorded_at=datetime.fromisoformat(data["dates"][i])
        )
        for i in range(len(data["dates"]))
    ]

@router.get("/{stock_id}/predict", response_model=StockPredictionResponse)
def stock_predict_get(stock_id: int, db: Session = Depends(get_db)):
    return stock.predict_stock(db, stock_id, use_post=False)


@router.post("/{stock_id}/predict", response_model=StockPredictionResponse)
def stock_predict_post(stock_id: int, db: Session = Depends(get_db)):
    return stock.predict_stock(db, stock_id, use_post=True)



@router.get("/top_gainers")
def top_gainers(limit: int = Query(10, gt=0), db: Session = Depends(get_db)):
    return stock.get_top_gainers(db, limit=limit)


@router.get("/{stock_id}/reviews", response_model=List[StockReviewResponse])
def get_reviews(stock_id: int, db: Session = Depends(get_db)):
    return stock.get_stock_reviews(db, stock_id)


@router.post("/{stock_id}/reviews", response_model=StockReviewResponse)
def create_review(
    stock_id: int,
    data: StockReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return stock.create_review(db, stock_id, data, current_user)



@router.get("/search", response_model=List[StockSchema])
def search_stocks(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, gt=0),
    db: Session = Depends(get_db),
):
    return stock.search_stocks(db, query, skip, limit)
