# app/schemas/news.py
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class NewsBase(BaseModel):
    title: str
    description: Optional[str]
    source: Optional[str]
    url: HttpUrl
    published_at: datetime
    stock_symbol: Optional[str] = None  # 특정 주식 관련 뉴스일 경우


class NewsCreate(NewsBase):
    """DB에 저장할 때 사용"""

    stock_id: Optional[int] = None


class NewsResponse(NewsBase):
    """API 응답용"""

    class Config:
        from_attributes = True
