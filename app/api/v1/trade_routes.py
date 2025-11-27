from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.trade import Trade as TradeSchema
from app.services.trade_executor import create_trade, get_user_trades

router = APIRouter()


@router.post("/", response_model=TradeSchema)
def create_trade_route(
    user_id: int, stock_id: int, quantity: int, db: Session = Depends(get_db)
):
    try:
        trade = create_trade(db, user_id, stock_id, quantity)
        return trade
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=List[TradeSchema])
def get_trades_route(user_id: int, db: Session = Depends(get_db)):
    return get_user_trades(db, user_id)
