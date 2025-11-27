from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.schemas.stock import (
    CountryResponse,
    MarketResponse,
    SectorResponse,
    StockResponse,
    StockReviewResponse,
    StockSchema,
    StockReviewCreate,
)
from app.services import stock
from app.core.security import get_current_user
from app.models.user import User

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
    return stock.get_stock_graph(db, stock_id)


@router.get("/{stock_id}/predict")
def stock_predict(stock_id: int, db: Session = Depends(get_db)):
    return stock.predict_stock(db, stock_id)


@router.get("/{stock_id}/reviews", response_model=List[StockReviewResponse])
def get_stock_reviews(stock_id: int, db: Session = Depends(get_db)):
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
def search_stocks(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return stock.search_stocks(db, query)
