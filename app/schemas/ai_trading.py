from pydantic import BaseModel
from datetime import datetime

class TradeResponse(BaseModel):
    id: int
    user_id: int
    stock_id: int
    action: str
    quantity: int
    price: float
    total_price: float
    created_at: datetime

    class Config:
        orm_mode = True