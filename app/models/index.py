

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from sqlalchemy.sql import func
from app.models.stock import Stock  # Stock import

# --- association table ---
index_component = Table(
    "index_component",
    Base.metadata,
    Column("index_id", Integer, ForeignKey("index.id"), primary_key=True),
    Column("stock_id", Integer, ForeignKey("stocks.id"), primary_key=True),
    Column("weight", Float),
)

# --- Index 모델 ---
class Index(Base):
    __tablename__ = "index"  # ✅ DB에 있는 이름과 매칭

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    symbol = Column(String, unique=True, nullable=False)

    market_id = Column(Integer, ForeignKey("markets.id"))
    current_value = Column(Float, default=0.0)
    change = Column(Float, default=0.0)

    # 관계
    values = relationship("IndexValue", back_populates="index", cascade="all, delete-orphan")
    components = relationship(
        "Stock", secondary=index_component, back_populates="indices"
    )

# --- IndexValue 모델 ---
class IndexValue(Base):
    __tablename__ = "index_value"

    id = Column(Integer, primary_key=True, index=True)
    index_id = Column(Integer, ForeignKey("index.id"))
    value = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    change_percent = Column(Float, default=0.0)

    index = relationship("Index", back_populates="values")


# --- Stock 모델에 relationship 추가 ---
Stock.indices = relationship(
    "Index", secondary=index_component, back_populates="components"
)
