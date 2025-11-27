from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import random

from app.db.session import get_db
from app.models.trade import Trade, UserAsset
from app.models.stock import SocialSentiment
from app.schemas.trade import TradeResponse, TradeHistoryResponse

router = APIRouter(prefix="/api/v1/ai_trading")

def run_ai_trading(db: Session, user_id: int):
    assets = db.query(UserAsset).filter(UserAsset.user_id == user_id).all()
    stocks_to_trade = [a.stock_id for a in assets] or [1, 2, 3]

    executed_trades = []

    for stock_id in stocks_to_trade:
        sentiments = db.query(SocialSentiment).filter(SocialSentiment.stock_id == stock_id).all()
        avg_sentiment = sum([s.sentiment_score for s in sentiments])/len(sentiments) if sentiments else 0

        if avg_sentiment > 0.2:
            action = "BUY"
            quantity = 10
            price = random.uniform(1000, 2000)
        elif avg_sentiment < -0.2:
            action = "SELL"
            quantity = 10
            price = random.uniform(1000, 2000)
        else:
            continue

        total_price = price * quantity

        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            price=price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )
        db.add(trade)

        asset = db.query(UserAsset).filter(
            UserAsset.user_id == user_id,
            UserAsset.stock_id == stock_id
        ).first()
        if not asset:
            asset = UserAsset(user_id=user_id, stock_id=stock_id)
            db.add(asset)

        if action == "BUY":
            asset.avg_price = ((asset.avg_price * asset.quantity) + total_price) / (asset.quantity + quantity) if asset.quantity else total_price/quantity
            asset.quantity += quantity
        elif action == "SELL":
            asset.quantity = max(asset.quantity - quantity, 0)

        executed_trades.append(TradeResponse(
            stock_id=stock_id,
            action=action,
            quantity=quantity,
            price=price,
            total_price=total_price
        ))

    db.commit()
    return executed_trades

@router.post("/run/{user_id}", response_model=List[TradeResponse])
def execute_ai_trading(user_id: int, db: Session = Depends(get_db)):
    trades = run_ai_trading(db, user_id)
    if not trades:
        return []
    return trades

@router.get("/history/{user_id}", response_model=List[TradeHistoryResponse])
def ai_trading_history(user_id: int, db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(Trade.user_id == user_id).all()
    if not trades:
        raise HTTPException(status_code=404, detail="No trading history found")
    return trades
