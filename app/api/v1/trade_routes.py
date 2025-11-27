from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.schemas.trade import TradeResponse, TradeHistoryResponse, Trade
from app.services import trade as trade_service
from app.core.security import get_current_user

router = APIRouter()



@router.post("/trade", response_model=TradeHistoryResponse)
def create_trade(
    stock_id: int = Query(..., gt=0),
    quantity: int = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    trade_obj = trade_service.create_trade(
        db=db,
        user_id=current_user.id,
        stock_id=stock_id,
        quantity=quantity
    )
    return trade_obj



@router.get("/trade/history", response_model=List[TradeHistoryResponse])
def get_trade_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    trades = trade_service.get_user_trades(db, current_user.id)
    return trades
