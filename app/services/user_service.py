import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, IdentityVerification
from app.models.user import UserWishlist

ANT_NAMES = [
    "갈고리머리개미",
    "곡예사개미",
    "모댁목수개미",
    "병정흰개미",
    "비시너스목수개미",
    "펜실베니커스목수개미",
    "흰발납자루개미",
    "미친개미",
    "유동성개미",
]


def generate_nickname(db: Session) -> str:
    while True:
        n = random.choice(ANT_NAMES)
        if not db.query(User).filter_by(nickname=n).first():
            return n


def generate_otp() -> str:
    return f"{random.randint(100000,999999)}"


def send_otp(user: User, db: Session):
    iv = user.identity_verification or IdentityVerification(user_id=user.id)
    iv.phone_code = generate_otp()
    iv.phone_attempt = 0
    iv.phone_expires = datetime.utcnow() + timedelta(minutes=5)
    db.add(iv)
    db.commit()
    db.refresh(iv)

    print(f"DEBUG: OTP for {user.phone} = {iv.phone_code}")
    return iv


def verify_otp(iv: IdentityVerification, code: str, db: Session):
    if iv.phone_attempt >= iv.max_attempt:
        raise Exception("Max attempts exceeded")
    if datetime.utcnow() > iv.phone_expires:
        raise Exception("OTP expired")
    iv.phone_attempt += 1
    if code != iv.phone_code:
        db.commit()
        raise Exception("Invalid OTP")
    iv.phone_verified = True
    iv.phone_expires = None
    db.commit()


def verify_identity(user: User, real_name: str, birth_date: datetime.date, db: Session):
    iv = user.identity_verification or IdentityVerification(user_id=user.id)
    iv.real_name = real_name
    iv.birth_date = birth_date
    iv.status = "verified"
    iv.verified_at = datetime.utcnow()
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return iv


def add_wishlist(db: Session, user_id: int, stock_id: int):
    item = UserWishlist(user_id=user_id, stock_id=stock_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_wishlist(db: Session, user_id: int, stock_id: int):
    item = (
        db.query(UserWishlist)
        .filter(UserWishlist.user_id == user_id, UserWishlist.stock_id == stock_id)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return item


def get_wishlist(db: Session, user_id: int):
    return db.query(UserWishlist).filter(UserWishlist.user_id == user_id).all()
