from pydantic import BaseModel, Field
from typing import List, Dict, Union
from datetime import datetime


class IndexValueSchema(BaseModel):
    value: float
    recorded_at: datetime
    change_percent: float

    class Config:
        orm_mode = True


class IndexBase(BaseModel):
    name: str
    market_id: int


class IndexCreate(IndexBase):
    components: Dict[int, float] = Field(default_factory=dict)


class IndexUpdate(IndexBase):
    components: Dict[int, float] = Field(default_factory=dict)


class IndexSchema(BaseModel):
    id: int
    name: str
    symbol: str
    market_id: int
    current_value: float
    change: float
    values: List[IndexValueSchema]
    components: Dict

    class MyModel(BaseModel):
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
    graph: Dict[str, List[Union[float, str]]]
    components: List[IndexGraphComponent]
