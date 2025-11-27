from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class IndexValueSchema(BaseModel):
    value: float
    recorded_at: datetime

    class Config:
        from_attributes = True


class IndexBase(BaseModel):
    name: str
    market_id: int


class IndexCreate(IndexBase):
    components: Dict[int, float] = {}


class IndexUpdate(IndexBase):
    components: Dict[int, float] = {}


class IndexSchema(IndexBase):
    id: int
    components: Dict[int, float] = {}
    values: List[IndexValueSchema] = []

    class Config:
        from_attributes = True


class IndexGraphComponent(BaseModel):
    id: int
    name: str
    weight: float


class IndexGraphResponse(BaseModel):
    index_id: int
    index_name: str
    market_id: int
    graph: Dict[str, List[float | str]]
    components: List[IndexGraphComponent]
