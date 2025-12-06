from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.schemas.news import NewsResponse
from app.services.news import fetch_and_save_news, get_news_by_stock, get_latest_news
from app.database import get_db

router = APIRouter()


@router.get("/popular", response_model=List[NewsResponse])
def get_popular_news(limit: int = Query(10, gt=0, le=50), db: Session = Depends(get_db)):
    """
    최신 뉴스 전체 조회 (DB에서 최신 순)
    """
    return get_latest_news(db, limit=limit)


@router.get("/search", response_model=List[NewsResponse])
def search_news(query: str = Query(..., min_length=1), limit: int = Query(10, gt=0, le=50), db: Session = Depends(get_db)):
    """
    검색어 기반 뉴스 조회 및 DB 저장
    """
    news_list = fetch_and_save_news(db, query=query, limit=limit)
    return news_list


@router.get("/stock/{symbol}", response_model=List[NewsResponse])
def get_stock_news(symbol: str, limit: int = Query(10, gt=0, le=50), db: Session = Depends(get_db)):
    """
    특정 주식 관련 뉴스 DB 조회
    """
    return get_news_by_stock(db, stock_symbol=symbol, limit=limit)


@router.get("/latest", response_model=List[NewsResponse])
def get_latest(limit: int = Query(10, gt=0, le=50), db: Session = Depends(get_db)):
    """
    DB에서 최신 뉴스 전체 조회
    """
    return get_latest_news(db, limit=limit)

