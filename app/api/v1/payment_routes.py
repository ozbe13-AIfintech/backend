from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.payment_service import create_payment_intent_service

router = APIRouter()


class PaymentCreate(BaseModel):
    amount: float
    currency: str = "usd"


@router.post("/create")
def create_payment(payment: PaymentCreate):
    try:
        client_secret = create_payment_intent_service(payment.amount, payment.currency)
        return {"client_secret": client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
