from fastapi import APIRouter, Query
from app.services.forex import get_exchange_rate
from app.schemas.forex import ExchangeRateResponse

router = APIRouter()

@router.get("/", response_model=ExchangeRateResponse)
def exchange_rate(
    base: str = Query("USD", min_length=3, max_length=3),
    target: str = Query("KRW", min_length=3, max_length=3)
):

    return get_exchange_rate(base, target)
