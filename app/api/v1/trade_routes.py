# app/api/v1/trades.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.services.trade_executor import get_user_owned_stocks
from app.schemas.trade import OwnedStockResponse
from app.db.session import get_db
from app.services.trade_executor import buy_stock, sell_stock, get_user_trades
from app.schemas.trade import TradeRequest, TradeResponse,TradeHistoryResponse
from app.core.security import get_current_user

router = APIRouter()

# --- 구매 ---
@router.post("/buy", response_model=TradeResponse)
def buy_trade(
    trade_in: TradeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # JWT 인증으로 사용자 가져오기
):
    trade = buy_stock(
        db=db,
        user_id=current_user.id,
        stock_id=trade_in.stock_id,
        quantity=trade_in.quantity,
    )
    return trade

# --- 판매 ---
@router.post("/sell", response_model=TradeResponse)
def sell_trade(
    trade_in: TradeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trade = sell_stock(
        db=db,
        user_id=current_user.id,
        stock_id=trade_in.stock_id,
        quantity=trade_in.quantity,
    )
    return trade

# --- 거래 내역 조회 ---
@router.get("/history", response_model=List[TradeHistoryResponse])
def trade_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trades = get_user_trades(db=db, user_id=current_user.id)
    return trades

@router.get("/users/my-stocks", response_model=List[OwnedStockResponse])
def my_stocks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    JWT 인증된 사용자의 보유 주식 조회
    """
    return get_user_owned_stocks(db, user_id=current_user.id)
