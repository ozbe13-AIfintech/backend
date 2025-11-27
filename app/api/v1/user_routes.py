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
from app.models.user import User, UserWishlist
from app.core import security
from app.services import user_service
from app.services.user_service import add_wishlist
from app.schemas.user import UserUpdateRequest
from fastapi import Security


router = APIRouter()


@router.post("/signup", response_model=UserResponse)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    if data.password != data.password_confirm:
        raise HTTPException(400, "Passwords do not match")
    if db.query(User).filter_by(phone=data.phone).first():
        raise HTTPException(400, "Phone already registered")
    u = User(
        phone=data.phone,
        hashed_password=security.hash_password(data.password),
        nickname=user_service.generate_nickname(db),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserResponse(id=u.id, nickname=u.nickname, phone=u.phone)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(phone=data.phone).first()
    if not u or not security.verify_password(data.password, u.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    token = security.create_jwt(u.id)
    return TokenResponse(token=token, nickname=u.nickname)


@router.post("/{user_id}/send_otp", response_model=MessageResponse)
def send_otp(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    user_service.send_otp(u, db)
    return MessageResponse(msg="OTP sent")


@router.post("/{user_id}/verify_otp", response_model=MessageResponse)
def verify_otp(user_id: int, data: OTPVerifyRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(id=user_id).first()
    if not u or not u.identity_verification:
        raise HTTPException(404, "OTP not found")
    try:
        user_service.verify_otp(u.identity_verification, data.code, db)
    except Exception as e:
        raise HTTPException(400, str(e))
    return MessageResponse(msg="Phone verified")


@router.post("/{user_id}/verify_identity", response_model=MessageResponse)
def verify_identity(
    user_id: int, data: IdentityVerifyRequest, db: Session = Depends(get_db)
):
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    user_service.verify_identity(u, data.real_name, data.birth_date, db)
    return MessageResponse(msg="Identity verified")


@router.post("/wishlist")
def add_to_wishlist(user_id: int, stock_id: int, db: Session = Depends(get_db)):
    return add_wishlist(db, user_id, stock_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user_profile(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Security(get_current_user),
    db: Session = Depends(get_db),
):

    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="본인만 수정할 수 있습니다.")

    if (
        not current_user.identity_verification
        or current_user.identity_verification.status != "verified"
    ):
        raise HTTPException(status_code=400, detail="본인 인증 후에만 수정 가능합니다.")

    if data.phone:
        current_user.phone = data.phone

    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id, nickname=current_user.nickname, phone=current_user.phone
    )


@router.get("/{user_id}/wishlist", response_model=WishlistResponse)
def get_user_wishlist(user_id: int, db: Session = Depends(get_db)):
    items = db.query(UserWishlist).filter(UserWishlist.user_id == user_id).all()
    return WishlistResponse(
        user_id=user_id,
        wishlist=[{"stock_id": i.stock_id, "stock_name": i.stock.name} for i in items],
    )
