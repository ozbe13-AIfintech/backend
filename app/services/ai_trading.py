# app/services/ai_trading.py
from sqlalchemy.orm import Session
from datetime import datetime
import random
from typing import List

from app.models.trade import Trade, UserAsset
from app.models.stock import SocialSentiment
from app.schemas.trade import TradeResponse
from fastapi import HTTPException

def run_ai_trading_service(db: Session, user_id: int) -> List[TradeResponse]:
    """
    로그인한 사용자의 AI 자동 거래 실행
    감성 점수가 0.2 이상이면 BUY, -0.2 이하이면 SELL, 중립은 PASS
    """
    assets = db.query(UserAsset).filter(UserAsset.user_id == user_id).all()
    stocks_to_trade = [a.stock_id for a in assets] or [1, 2, 3]

    executed_trades = []

    for stock_id in stocks_to_trade:
        sentiments = db.query(SocialSentiment).filter(SocialSentiment.stock_id == stock_id).all()
        avg_sentiment = sum([s.sentiment_score for s in sentiments]) / len(sentiments) if sentiments else 0

        if avg_sentiment > 0.2:
            quantity = 10  # BUY
            price = random.uniform(100, 500)
        elif avg_sentiment < -0.2:
            quantity = -10  # SELL
            price = random.uniform(100, 500)
        else:
            continue

        total_price = price * abs(quantity)

        # Trade DB 저장 (action 제거)
        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            price=price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        # UserAsset 업데이트
        asset = db.query(UserAsset).filter(UserAsset.user_id == user_id, UserAsset.stock_id == stock_id).first()
        if not asset:
            asset = UserAsset(user_id=user_id, stock_id=stock_id, avg_price=price, quantity=0)
            db.add(asset)

        if quantity > 0:  # BUY
            asset.avg_price = ((asset.avg_price * asset.quantity) + total_price) / (asset.quantity + quantity) if asset.quantity else price
            asset.quantity += quantity
        else:  # SELL
            asset.quantity = max(asset.quantity + quantity, 0)  # quantity < 0 이므로 더하기

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
    trades = db.query(Trade).filter(Trade.user_id == user_id).order_by(Trade.created_at.desc()).all()
    return trades
