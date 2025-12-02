from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.services.ai_trading import (
    run_ai_trading_service,
    get_ai_trading_history_service,
)
from app.schemas.trade import TradeResponse, TradeHistoryResponse

router = APIRouter(prefix="/api/v1/ai_trading", tags=["AI_Trading"])


@router.post("/run/{user_id}", response_model=List[TradeResponse])
def execute_ai_trading(user_id: int, db: Session = Depends(get_db)):
    trades = run_ai_trading_service(db, user_id)
    return trades


@router.get("/history/{user_id}", response_model=List[TradeHistoryResponse])
def ai_trading_history(user_id: int, db: Session = Depends(get_db)):
    trades = get_ai_trading_history_service(db, user_id)
    if not trades:
        raise HTTPException(status_code=404, detail="No trading history found")
    return trades
