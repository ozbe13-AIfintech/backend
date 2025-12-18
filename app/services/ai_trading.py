from sqlalchemy.orm import Session
from datetime import datetime
import random
from typing import List

from fastapi import HTTPException

from app.models.user import User
from app.models.trade import Trade, UserAsset
from app.models.stock import SocialSentiment
from app.schemas.trade import TradeResponse


def run_ai_trading_service(db: Session, user_id: int) -> List[TradeResponse]:

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    assets = db.query(UserAsset).filter(UserAsset.user_id == user_id).all()
    stocks_to_trade = [a.stock_id for a in assets] or [1, 2, 3]

    executed_trades: List[TradeResponse] = []

    for stock_id in stocks_to_trade:
        sentiments = (
            db.query(SocialSentiment)
            .filter(SocialSentiment.stock_id == stock_id)
            .all()
        )
        avg_sentiment = (
            sum(s.sentiment_score for s in sentiments) / len(sentiments)
            if sentiments
            else 0
        )


        if avg_sentiment > 0.2:
            quantity = 10
        elif avg_sentiment < -0.2:
            quantity = -10
        else:
            continue

        price = random.uniform(100, 500)
        total_price = price * abs(quantity)


        asset = (
            db.query(UserAsset)
            .filter(
                UserAsset.user_id == user_id,
                UserAsset.stock_id == stock_id,
            )
            .first()
        )


        if quantity > 0:
            if user.balance < total_price:
                continue

            user.balance -= total_price

            if not asset:
                asset = UserAsset(
                    user_id=user_id,
                    stock_id=stock_id,
                    avg_price=price,
                    quantity=0,
                )
                db.add(asset)

            asset.avg_price = (
                ((asset.avg_price * asset.quantity) + total_price)
                / (asset.quantity + quantity)
                if asset.quantity > 0
                else price
            )
            asset.quantity += quantity


        else:
            if not asset or asset.quantity < abs(quantity):
                continue

            user.balance += total_price
            asset.quantity -= abs(quantity)

            if asset.quantity == 0:
                asset.avg_price = 0

        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            price=price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )

        db.add(trade)
        db.flush()
        executed_trades.append(
            TradeResponse(
                id=trade.id,
                user_id=trade.user_id,
                stock_id=trade.stock_id,
                action="BUY" if quantity > 0 else "SELL",
                quantity=abs(quantity),
                price=price,
                total_price=total_price,
                created_at=trade.created_at,
            )
        )

    db.commit()
    return executed_trades


def get_ai_trading_history_service(db: Session, user_id: int) -> List[Trade]:
    """
    사용자의 AI 거래 히스토리 조회
    """
    return (
        db.query(Trade)
        .filter(Trade.user_id == user_id)
        .order_by(Trade.created_at.desc())
        .all()
    )
