from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ai_trading import run_ai_trading
from app.models.trade import Trade
from app.schemas.trade import TradeHistoryResponse,TradeResponse
from typing import  List


router = APIRouter(prefix="/api/v1/ai_trading", tags=["AI_Trading"])

@router.post("/run/{user_id}")
def execute_ai_trading(user_id: int, db: Session = Depends(get_db)):
    trades = run_ai_trading(db, user_id)
    if not trades:
        return {"msg": "No trades executed"}
    return {"msg": "AI trading executed", "trades": trades}

@router.get("/history/{user_id}")
def ai_trading_history(user_id: int, db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(Trade.user_id==user_id).all()
    if not trades:
        raise HTTPException(status_code=404, detail="No trading history found")
    return trades



@router.post("/run/{user_id}", response_model=List[TradeResponse])
def execute_ai_trading(user_id: int, db: Session = Depends(get_db)):
    trades = run_ai_trading(db, user_id)
    return trades

@router.get("/history/{user_id}", response_model=List[TradeHistoryResponse])
def ai_trading_history(user_id: int, db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(Trade.user_id==user_id).all()
    if not trades:
        raise HTTPException(status_code=404, detail="No trading history found")
    return trades

