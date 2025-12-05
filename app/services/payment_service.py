from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User


def charge_card(card_number: str, expiry_date: str, cvc: str, amount: float) -> bool:
    """
    카드 결제 시뮬레이션
    실제 PG사 연동 시 API 호출
    """
    print(f"Charging card {card_number} for {amount}원")
    return True


def deposit_to_user(db: Session, user: User, amount: float, card_number: str, expiry_date: str, cvc: str):
    if not getattr(user, "is_verified", False):
        raise HTTPException(status_code=403, detail="본인 인증이 필요합니다.")

    success = charge_card(card_number, expiry_date, cvc, amount)
    if not success:
        raise HTTPException(status_code=400, detail="카드 결제 실패")

    user.balance += amount
    db.commit()
    return user.balance
