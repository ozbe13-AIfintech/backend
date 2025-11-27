from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.payment_service import create_payment_intent, handle_webhook_event
from app.db.session import get_db
import stripe
import os

router = APIRouter()


class PaymentCreate(BaseModel):
    amount: float
    currency: str = "usd"


@router.post("/create")
def create_payment(payment: PaymentCreate):
    client_secret = create_payment_intent(payment.amount, payment.currency)
    return {"client_secret": client_secret}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe 웹훅 이벤트 수신
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    result = handle_webhook_event(event, db)
    return result
