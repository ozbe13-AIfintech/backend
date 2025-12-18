from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FraudLogResponse(BaseModel):
    user_id: int
    stock_id: int


    stock_name: str
    stock_symbol: str

    risk_score: float
    reason: str
    price_change: Optional[float]
    volume_change: Optional[float]
    average_price: Optional[float]
    average_volume: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
