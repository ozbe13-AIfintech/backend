from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.ai_trading import (
    run_ai_trading_service,
    get_ai_trading_history_service,
)
from app.db.session import get_db
from app.schemas.trade import TradeResponse
from app.core.security import get_current_user

router = APIRouter()


@router.post("/run/", response_model=list[TradeResponse])
def execute_ai_trading(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return run_ai_trading_service(db, current_user.id)


@router.get("/history/", response_model=list[TradeResponse])
def get_ai_trading_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trades = get_ai_trading_history_service(db, current_user.id)

    response = [
        TradeResponse(
            id=t.id,
            user_id=t.user_id,
            stock_id=t.stock_id,
            action="BUY" if t.quantity > 0 else "SELL",
            quantity=abs(t.quantity),
            price=t.price,
            total_price=t.total_price,
            created_at=t.created_at,
        )
        for t in trades
    ]
    return response
