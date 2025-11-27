from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.schemas.user import (
    SignupRequest,
    LoginRequest,
    OTPVerifyRequest,
    IdentityVerifyRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
    WishlistResponse,
)
from app.models.user import User

from app.services import user_service

from app.schemas.user import UserUpdateRequest
from fastapi import Security


router = APIRouter()

@router.post("/signup", response_model=UserResponse)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    user = user_service.signup(db, data)
    return UserResponse(
        id=user.id,
        nickname=user.nickname,
        phone=user.phone
    )



@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token, nickname = user_service.login(db, data)
    return TokenResponse(token=token, nickname=nickname)



@router.post("/{user_id}/send_otp", response_model=MessageResponse)
def send_otp(user_id: int, db: Session = Depends(get_db)):
    user_service.send_otp(db, user_id)
    return MessageResponse(msg="OTP sent")



@router.post("/{user_id}/verify_otp", response_model=MessageResponse)
def verify_otp(user_id: int, data: OTPVerifyRequest, db: Session = Depends(get_db)):
    user_service.verify_otp(db, user_id, data.code)
    return MessageResponse(msg="Phone verified")



@router.post("/{user_id}/verify_identity", response_model=MessageResponse)
def verify_identity(
    user_id: int,
    data: IdentityVerifyRequest,
    db: Session = Depends(get_db)
):
    user_service.verify_identity(db, user_id, data.real_name, data.birth_date)
    return MessageResponse(msg="Identity verified")


@router.post("/wishlist", response_model=WishlistResponse)
def add_to_wishlist(user_id: int, stock_id: int, db: Session = Depends(get_db)):
    wishlist = user_service.add_wishlist(db, user_id, stock_id)
    return WishlistResponse(
        user_id=user_id,
        wishlist=wishlist
    )



@router.put("/{user_id}", response_model=UserResponse)
def update_user_profile(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Security(get_current_user),
    db: Session = Depends(get_db),
):
    updated = user_service.update_user_profile(db, user_id, data, current_user)
    return UserResponse(
        id=updated.id,
        nickname=updated.nickname,
        phone=updated.phone
    )



@router.get("/{user_id}/wishlist", response_model=WishlistResponse)
def get_user_wishlist(user_id: int, db: Session = Depends(get_db)):
    wishlist = user_service.get_wishlist(db, user_id)
    return WishlistResponse(user_id=user_id, wishlist=wishlist)

@router.get("/{user_id}", summary="Get user profile")
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user_profile(db, user_id)


@router.delete("/{user_id}/wishlist/{stock_id}", summary="Remove item from wishlist")
def remove_wishlist_item(user_id: int, stock_id: int, db: Session = Depends(get_db)):
    return user_service.remove_wishlist_item(db, user_id, stock_id)