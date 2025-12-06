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
from sqlalchemy import BigInteger


class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    markets = relationship("Market", back_populates="country")
    stocks = relationship("Stock", back_populates="country")


class Market(Base):
    __tablename__ = "markets"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    created_at = Column(DateTime, server_default=func.now())
    country = relationship("Country", back_populates="markets")
    stocks = relationship("Stock", back_populates="market")


class Sector(Base):
    __tablename__ = "sectors"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    stocks = relationship("Stock", back_populates="sector")


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    symbol = Column(String(50), unique=True, nullable=False)
    sector_id = Column(Integer, ForeignKey("sectors.id"))
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    market_id = Column(Integer, ForeignKey("markets.id"))
    created_at = Column(DateTime, server_default=func.now())

    sector = relationship("Sector", back_populates="stocks")
    country = relationship("Country", back_populates="stocks")
    market = relationship("Market", back_populates="stocks")
    prices = relationship("StockPrice", back_populates="stock")
    predictions = relationship("StockPrediction", back_populates="stock")
    reviews = relationship("StockReview", back_populates="stock")
    sentiments = relationship("SocialSentiment", back_populates="stock")
    fraud_logs = relationship("FraudLog", back_populates="stock")
    user_wishlist = relationship("UserWishlist", back_populates="stock")
    news = relationship("News", back_populates="stock")


class StockPrice(Base):
    __tablename__ = "stock_prices"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(BigInteger)
    market_cap = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    market_index = Column(Float)
    market_index_change = Column(Float)
    recorded_at = Column(DateTime, nullable=False)

    stock = relationship("Stock", back_populates="prices")

    @classmethod
    def get_latest_price(cls, db_session, stock_id: int):
        return (
            db_session.query(cls)
            .filter(cls.stock_id == stock_id)
            .order_by(cls.recorded_at.desc())
            .first()
        )


class StockPrediction(Base):
    __tablename__ = "stock_predictions"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    prediction = Column(Float)
    model_name = Column(String(255))
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    stock = relationship("Stock", back_populates="predictions")


class StockReview(Base):
    __tablename__ = "stock_reviews"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text)
    rating = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    stock = relationship("Stock", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


class SocialSentiment(Base):
    __tablename__ = "social_sentiments"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    source = Column(String(255))
    sentiment_score = Column(Float)
    content = Column(Text)
    recorded_at = Column(DateTime, server_default=func.now())

    stock = relationship("Stock", back_populates="sentiments")

    def __repr__(self):
        return f"<SocialSentiment(stock_id={self.stock_id}, score={self.sentiment_score}, source={self.source})>"
