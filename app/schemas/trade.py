# app/schemas/trade.py
from pydantic import BaseModel
from datetime import datetime


class TradeRequest(BaseModel):
    stock_id: int
    quantity: int


class TradeResponse(BaseModel):
    id: int
    user_id: int
    stock_id: int
    quantity: int
    price: float
    total_price: float
    created_at: datetime

    class Config:
        orm_mode = True


class TradeHistoryResponse(BaseModel):
    id: int
    user_id: int
    stock_id: int
    quantity: int
    price: float
    total_price: float
    created_at: datetime

    class Config:
        orm_mode = True


class OwnedStockResponse(BaseModel):
    id: int
    name: str
    symbol: str
    quantity: int
    avg_price: float
    current_price: float  # 필요하면 실시간 시세 포함
