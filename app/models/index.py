from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


index_component = Table(
    "index_component",
    Base.metadata,
    Column("index_id", Integer, ForeignKey("index.id"), primary_key=True),
    Column("stock_id", Integer, ForeignKey("stocks.id"), primary_key=True),
    Column("weight", Float),
)


class Index(Base):
    __tablename__ = "index"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    market_id = Column(Integer, ForeignKey("markets.id"))
    current_value = Column(Float)
    change = Column(Float)
    values = relationship("IndexValue", back_populates="index")
    components = relationship(
        "Stock", secondary=index_component, back_populates="indices"
    )


class IndexValue(Base):
    __tablename__ = "index_value"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(Integer, ForeignKey("index.id"))
    value = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    index = relationship("Index", back_populates="values")


from app.models.stock import Stock

Stock.indices = relationship(
    "Index", secondary=index_component, back_populates="components"
)
