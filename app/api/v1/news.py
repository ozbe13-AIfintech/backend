from fastapi import APIRouter, Query
from typing import List, Optional
from app.schemas.news import NewsResponse
from app.services.news import fetch_popular_stock_news, search_stock_news

router = APIRouter(prefix="/news", tags=["News"])

# 인기 뉴스
@router.get("/popular", response_model=List[NewsResponse])
def get_popular_news(limit: int = Query(10, gt=0, le=50)):
    return fetch_popular_stock_news(limit=limit)

# 검색 뉴스
@router.get("/search", response_model=List[NewsResponse])
def search_news(query: str = Query(..., min_length=1), limit: int = Query(10, gt=0, le=50)):
    return search_stock_news(query=query, limit=limit)
