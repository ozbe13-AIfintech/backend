from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    BigInteger,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class FraudLog(Base):
    __tablename__ = "fraud_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=True)
    risk_score = Column(Float, nullable=False)
    reason = Column(String(255))
    price_change = Column(Float, nullable=True)  # 가격 변화
    volume_change = Column(Float, nullable=True)  # 거래량 변화
    average_price = Column(Float, nullable=True)  # 평균 가격
    average_volume = Column(Float, nullable=True)  # 평균 거래량
    created_at = Column(DateTime, server_default=func.now())
    stock = relationship("Stock", back_populates="fraud_logs")
