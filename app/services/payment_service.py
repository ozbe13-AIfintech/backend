import stripe
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.db.session import get_db

stripe.api_key = os.getenv("STRIPE_API_KEY")


def create_payment_intent(amount: float, currency: str = "usd") -> str:
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            payment_method_types=["card"],
        )
        return intent.client_secret
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def handle_webhook_event(event: dict, db: Session):

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if event_type == "payment_intent.succeeded":

        user_id = data.get("metadata", {}).get("user_id")
        amount_received = data.get("amount_received", 0) / 100  # 달러로 변환

        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user:

                user.balance = getattr(user, "balance", 0) + amount_received
                db.commit()

        return {"status": "success", "amount": amount_received, "user_id": user_id}

    elif event_type == "payment_intent.payment_failed":
        return {"status": "failed", "reason": data.get("last_payment_error", {}).get("message")}

    return {"status": "ignored", "event_type": event_type}
