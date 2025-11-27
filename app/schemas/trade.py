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
