from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(128), nullable=True)
    url = Column(String(512), nullable=False, unique=True)
    published_at = Column(DateTime, nullable=False)
    stock_symbol = Column(String(16), nullable=True)

    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=True)
    stock = relationship("Stock", back_populates="news")
    sentiments = relationship("SocialSentiment", back_populates="news")

    def __repr__(self):
        return f"<News(title={self.title}, source={self.source}, published_at={self.published_at})>"
