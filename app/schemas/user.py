from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from datetime import datetime


class SignupRequest(BaseModel):
    phone: str
    password: str
    password_confirm: str


class LoginRequest(BaseModel):
    phone: str
    password: str


class OTPVerifyRequest(BaseModel):
    code: str


class IdentityVerifyRequest(BaseModel):
    real_name: str
    birth_date: date


class UserResponse(BaseModel):
    id: int
    nickname: str
    phone: str


class MessageResponse(BaseModel):
    msg: str


class UserUpdateRequest(BaseModel):
    nickname: Optional[str]
    phone: Optional[str]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    nickname: str
    user_id: int


class WishlistAddRequest(BaseModel):
    stock_id: int
    favorite: bool


class WishlistItem(BaseModel):
    stock_id: int
    stock_name: str


class WishlistResponse(BaseModel):
    user_id: int
    wishlist: List[WishlistItem]


class UserWishlistBase(BaseModel):
    stock_id: int


class UserWishlistCreate(UserWishlistBase):
    pass


class UserWishlist(UserWishlistBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
