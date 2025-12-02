from pydantic import BaseModel
from datetime import datetime


from pydantic import BaseModel
from datetime import datetime

class ExchangeRateResponse(BaseModel):
    base_currency: str
    target_currency: str
    rate: float
    last_updated: datetime
    source: str = "exchangerate.host"  # 추가된 필드: 환율 제공 API 소스

    class Config:
        from_attributes = True

