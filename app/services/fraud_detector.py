from app.models.fraud import FraudLog
from app.models.stock import StockPrice
from sqlalchemy.orm import Session
from typing import Optional, List
import numpy as np


def determine_risk_level(risk_score: float) -> str:
    if risk_score >= 80:
        return "High"
    elif risk_score >= 40:
        return "Medium"
    else:
        return "Low"


def get_fraud_logs(db: Session, stock_id: Optional[int] = None) -> List[FraudLog]:

    query = db.query(FraudLog)
    if stock_id:
        query = query.filter(FraudLog.stock_id == stock_id)
    return query.all()


def detect_fraud(db: Session, stock_id: int, user_id: int) -> FraudLog:

    prices = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at.desc())
        .limit(5)
        .all()
    )
    if not prices:
        return None

    risk_score = 0
    reason = []

    if len(prices) >= 2:
        price_change = abs(prices[0].price - prices[1].price) / prices[1].price
        if price_change > 0.1:
            risk_score += 50
            reason.append("Price spike detected")

        volume_change = (prices[0].volume or 0) - (prices[1].volume or 0)
        if (
            prices[1].volume and volume_change / prices[1].volume > 2
        ):  # 거래량 2배 이상 증가
            risk_score += 50
            reason.append("Volume spike detected")

    # 평균 가격 및 평균 거래량 계산
    average_price = np.mean([p.price for p in prices])
    average_volume = np.mean([p.volume or 0 for p in prices])

    # 위험 수준 계산
    risk_level = determine_risk_level(risk_score)

    # FraudLog 저장
    fraud_log = FraudLog(
        user_id=user_id,
        stock_id=stock_id,
        risk_score=risk_score,
        reason=", ".join(reason) if reason else "No issues detected",
        price_change=price_change,
        volume_change=volume_change,
        average_price=average_price,
        average_volume=average_volume,
    )
    db.add(fraud_log)
    db.commit()
    db.refresh(fraud_log)

    return fraud_log, risk_level
