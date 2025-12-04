from sqlalchemy import Column, Integer, String, Float, DateTime

from datetime import datetime
from app.db.base import Base



class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True)
    base_currency = Column(String(3), nullable=False)  # 예: USD, EUR
    target_currency = Column(String(3), nullable=False)  # 예: KRW, JPY
    rate = Column(Float, nullable=False)  # 환율 값 (예: 1300.75)
    last_updated = Column(DateTime, default=datetime.utcnow)  # 마지막 갱신 시간
    source = Column(String(100), nullable=True)  # 환율 제공 API 또는 소스 (예: 'exchangerate.host')

    def __repr__(self):
        return f"<ExchangeRate(base_currency={self.base_currency}, target_currency={self.target_currency}, rate={self.rate}, last_updated={self.last_updated})>"


class ExchangeRateHistory(Base):
    __tablename__ = "exchange_rate_history"

    id = Column(Integer, primary_key=True)
    base_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)  # 기록된 시간

    def __repr__(self):
        return f"<ExchangeRateHistory(base_currency={self.base_currency}, target_currency={self.target_currency}, rate={self.rate}, timestamp={self.timestamp})>"
