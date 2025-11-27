import stripe
import os

stripe.api_key = os.getenv("STRIPE_API_KEY")


def create_payment_intent_service(amount: float, currency: str = "usd"):
    intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),  # 센트 단위
        currency=currency,
        payment_method_types=["card"],
    )
    return intent.client_secret
