from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.services.payment_service import deposit_to_user

router = APIRouter()


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0)
    card_number: str = Field(..., min_length=12, max_length=19)
    expiry_date: str
    cvc: str


@router.post("/deposit")
def deposit(
    data: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    balance = deposit_to_user(
        db=db,
        user=current_user,
        amount=data.amount,
        card_number=data.card_number,
        expiry_date=data.expiry_date,
        cvc=data.cvc,
    )
    return {"msg": f"{data.amount}원이 충전되었습니다.", "balance": balance}


@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return {"balance": current_user.balance}
