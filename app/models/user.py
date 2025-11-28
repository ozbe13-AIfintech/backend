from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Float,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    balance = Column(Float, default=0.0)
    identity_verification = relationship(
        "IdentityVerification", uselist=False, back_populates="user"
    )
    trades = relationship("Trade", back_populates="user")
    assets = relationship("UserAsset", back_populates="user")
    wishlist = relationship("UserWishlist", back_populates="user")


class IdentityVerification(Base):
    __tablename__ = "identity_verifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    real_name = Column(String(50))
    birth_date = Column(Date)
    phone_verified = Column(Boolean, default=False)
    phone_code = Column(String(6))
    phone_attempt = Column(Integer, default=0)
    max_attempt = Column(Integer, default=3)
    phone_expires = Column(DateTime)
    status = Column(String(20), default="pending")
    verified_at = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="identity_verification")


class UserWishlist(Base):
    __tablename__ = "user_wishlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wishlist")
    stock = relationship("Stock")
