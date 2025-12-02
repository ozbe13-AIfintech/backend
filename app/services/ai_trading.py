from sqlalchemy.orm import Session
from datetime import datetime
import random
from typing import List

from app.models.trade import Trade, UserAsset
from app.models.stock import SocialSentiment
from app.schemas.trade import TradeResponse


def run_ai_trading_service(db: Session, user_id: int) -> List[TradeResponse]:
    # 사용자의 자산 조회
    assets = db.query(UserAsset).filter(UserAsset.user_id == user_id).all()
    stocks_to_trade = [a.stock_id for a in assets] or [1, 2, 3]

    executed_trades = []

    for stock_id in stocks_to_trade:
        # 감성 분석 기반 의사결정
        sentiments = (
            db.query(SocialSentiment).filter(SocialSentiment.stock_id == stock_id).all()
        )
        avg_sentiment = (
            sum([s.sentiment_score for s in sentiments]) / len(sentiments)
            if sentiments
            else 0
        )

        if avg_sentiment > 0.2:
            action = "BUY"
            quantity = 10
            price = random.uniform(1000, 2000)
        elif avg_sentiment < -0.2:
            action = "SELL"
            quantity = 10
            price = random.uniform(1000, 2000)
        else:
            continue  # 중립 감성은 거래하지 않음

        total_price = price * quantity

        # Trade 기록 생성
        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            price=price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )
        db.add(trade)

        # UserAsset 업데이트
        asset = (
            db.query(UserAsset)
            .filter(UserAsset.user_id == user_id, UserAsset.stock_id == stock_id)
            .first()
        )
        if not asset:
            asset = UserAsset(user_id=user_id, stock_id=stock_id)
            db.add(asset)

        if action == "BUY":
            asset.avg_price = (
                ((asset.avg_price * asset.quantity) + total_price)
                / (asset.quantity + quantity)
                if asset.quantity
                else total_price / quantity
            )
            asset.quantity += quantity
        elif action == "SELL":
            asset.quantity = max(asset.quantity - quantity, 0)

        executed_trades.append(
            TradeResponse(
                stock_id=stock_id,
                action=action,
                quantity=quantity,
                price=price,
                total_price=total_price,
            )
        )

    db.commit()
    return executed_trades


def get_ai_trading_history_service(db: Session, user_id: int):
    trades = db.query(Trade).filter(Trade.user_id == user_id).all()
    return trades
