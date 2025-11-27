from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NewsResponse(BaseModel):
    title: str
    description: Optional[str]
    source: Optional[str]
    url: Optional[str]
    published_at: datetime

    class Config:
        from_attributes = True
