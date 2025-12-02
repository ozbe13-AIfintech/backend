from pydantic import BaseModel
from datetime import datetime


class Trade(BaseModel):
    id: int
    user_id: int
    stock_id: int
    quantity: int
    price: float
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    stock_id: int
    action: str
    quantity: int
    price: float
    total_price: float

    class Config:
        from_attributes = True


class TradeHistoryResponse(BaseModel):
    id: int
    user_id: int
    stock_id: int
    quantity: int
    price: float
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True
