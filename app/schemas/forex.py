from pydantic import BaseModel
from datetime import datetime

class ExchangeRateResponse(BaseModel):
    base_currency: str
    target_currency: str
    rate: float
    last_updated: datetime

    class Config:
        from_attributes = True
