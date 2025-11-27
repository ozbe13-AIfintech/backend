import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User, IdentityVerification, UserWishlist
from app.core import security
from app.schemas.user import SignupRequest, LoginRequest, UserUpdateRequest



ANT_NAMES = [
    "갈고리머리개미", "곡예사개미", "모댁목수개미", "병정흰개미",
    "비시너스목수개미", "펜실베니커스목수개미", "흰발납자루개미",
    "미친개미", "유동성개미",
]


def generate_nickname(db: Session) -> str:
    while True:
        n = random.choice(ANT_NAMES)
        if not db.query(User).filter_by(nickname=n).first():
            return n


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"



def signup(db: Session, data: SignupRequest) -> User:
    if data.password != data.password_confirm:
        raise HTTPException(400, "Passwords do not match")

    if db.query(User).filter_by(phone=data.phone).first():
        raise HTTPException(400, "Phone already registered")

    user = User(
        phone=data.phone,
        hashed_password=security.hash_password(data.password),
        nickname=generate_nickname(db),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, data: LoginRequest):
    user = db.query(User).filter_by(phone=data.phone).first()

    if not user or not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")

    token = security.create_jwt(user.id)
    return token, user.nickname



def send_otp(db: Session, user_id: int):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    iv = user.identity_verification or IdentityVerification(user_id=user.id)

    iv.phone_code = generate_otp()
    iv.phone_attempt = 0
    iv.phone_expires = datetime.utcnow() + timedelta(minutes=5)

    db.add(iv)
    db.commit()


    print(f"DEBUG OTP for {user.phone} = {iv.phone_code}")



def verify_otp(db: Session, user_id: int, code: str):
    user = db.query(User).filter_by(id=user_id).first()
    if not user or not user.identity_verification:
        raise HTTPException(404, "OTP not found")

    iv = user.identity_verification

    if iv.phone_attempt >= iv.max_attempt:
        raise HTTPException(400, "Max attempts exceeded")

    if datetime.utcnow() > iv.phone_expires:
        raise HTTPException(400, "OTP expired")

    iv.phone_attempt += 1

    if code != iv.phone_code:
        db.commit()
        raise HTTPException(400, "Invalid OTP")

    iv.phone_verified = True
    iv.phone_expires = None

    db.commit()



def verify_identity(db: Session, user_id: int, real_name: str, birth_date,):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    iv = user.identity_verification or IdentityVerification(user_id=user_id)

    iv.real_name = real_name
    iv.birth_date = birth_date
    iv.status = "verified"
    iv.verified_at = datetime.utcnow()

    db.add(iv)
    db.commit()
    db.refresh (iv)


def add_wishlist(db: Session, user_id: int, stock_id: int):
    item = UserWishlist(user_id=user_id, stock_id=stock_id)

    db.add(item)
    db.commit()
    db.refresh(item)

    return get_wishlist(db, user_id)



def get_wishlist(db: Session, user_id: int):
    items = db.query(UserWishlist).filter(UserWishlist.user_id == user_id).all()
    return [
        {"stock_id": i.stock_id, "stock_name": i.stock.name}
        for i in items
    ]



def update_user_profile(
    db: Session,
    user_id: int,
    data: UserUpdateRequest,
    current_user: User
):
    if current_user.id != user_id:
        raise HTTPException(403, "본인만 수정할 수 있습니다.")

    if (
        not current_user.identity_verification
        or current_user.identity_verification.status != "verified"
    ):
        raise HTTPException(400, "본인 인증 후에만 수정 가능합니다.")


    if data.phone:
        current_user.phone = data.phone

    db.commit()
    db.refresh(current_user)

    return current_user
