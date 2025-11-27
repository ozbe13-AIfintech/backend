from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CountryResponse(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class MarketResponse(BaseModel):
    id: int
    name: str
    country_id: int

    class Config:
        from_attributes = True


class SectorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class StockSchema(BaseModel):
    id: int
    name: str
    price: float


class StockResponse(BaseModel):
    id: int
    name: str
    symbol: str
    country_id: int
    market_id: Optional[int]
    sector_id: Optional[int]

    class Config:
        from_attributes = True


class StockPriceResponse(BaseModel):
    price: float
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]
    market_cap: Optional[float]
    market_index: Optional[float]
    market_index_change: Optional[float]
    recorded_at: datetime

    class Config:
        from_attributes = True


class StockPredictionResponse(BaseModel):
    prediction: float
    model_name: Optional[str]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class StockReviewResponse(BaseModel):
    content: str
    rating: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class SocialSentimentResponse(BaseModel):
    source: Optional[str]
    sentiment_score: Optional[float]
    content: Optional[str]
    recorded_at: datetime

    class Config:
        from_attributes = True


class FraudLogResponse(BaseModel):
    risk_score: float
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Stock(BaseModel):
    id: int
    name: str
    ticker: str

    class Config:
        from_attributes = True


class StockReviewCreate(BaseModel):
    content: str
    rating: Optional[int]
