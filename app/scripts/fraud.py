from app.models.fraud import FraudLog
from app.models.stock import Stock, StockPrice
from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
import numpy as np
from app.db.session import SessionLocal



def determine_risk_level(risk_score: float) -> str:
    if risk_score >= 80:
        return "High"
    elif risk_score >= 40:
        return "Medium"
    return "Low"


def detect_fraud_service(
    db: Session, stock_id: int, user_id: int
) -> Tuple[Optional[FraudLog], str]:
    try:
        prices = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock_id)
            .order_by(StockPrice.recorded_at.desc())
            .limit(5)
            .all()
        )

        if not prices:
            return None, "Low"

        risk_score = 0
        reason = []

        price_change: Optional[float] = None
        volume_change: Optional[float] = None

        if len(prices) >= 2:
            last = prices[0]
            prev = prices[1]

            if prev.price > 0:
                price_change = abs(float(last.price) - float(prev.price)) / float(
                    prev.price
                )
                price_change = float(price_change)
                if price_change > 0.1:
                    risk_score += 50
                    reason.append("Price spike detected")

            if prev.volume:
                volume_change = (float(last.volume) - float(prev.volume)) / float(
                    prev.volume
                )
                volume_change = float(volume_change)
                if volume_change > 2:
                    risk_score += 50
                    reason.append("Volume spike detected")

        average_price = float(np.mean([float(p.price) for p in prices]))
        average_volume = float(np.mean([float(p.volume) for p in prices]))

        if not reason:
            reason = ["No significant anomalies detected"]

        fraud_log = FraudLog(
            user_id=int(user_id),
            stock_id=int(stock_id),
            risk_score=float(risk_score),
            reason=", ".join(reason),
            price_change=price_change,
            volume_change=volume_change,
            average_price=average_price,
            average_volume=average_volume,
        )

        db.add(fraud_log)
        db.commit()
        db.refresh(fraud_log)

        risk_level = determine_risk_level(risk_score)
        return fraud_log, risk_level

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 오류 발생: {e}")
        return None, "Low"


def detect_multiple_fraud_service(
    db: Session, stock_ids: List[int], user_id: int
) -> List[FraudLog]:
    fraud_logs = []
    for stock_id in stock_ids:
        fraud_log, _ = detect_fraud_service(db, stock_id, user_id)
        if fraud_log:
            fraud_logs.append(fraud_log)
    return fraud_logs



def run_fraud_batch(user_id: int = 1):
    db: Session = SessionLocal()
    try:

        stock_ids = [s.id for s in db.query(Stock).all()]
        print(f"[INFO] Total stocks: {len(stock_ids)}")


        fraud_logs = detect_multiple_fraud_service(db, stock_ids, user_id)
        print(f"[INFO] Fraud detection completed. Logs created: {len(fraud_logs)}")

        for log in fraud_logs:
            print(
                f"- Stock {log.stock_id} | Risk {log.risk_score} | Reason: {log.reason} | "
                f"Price Change: {log.price_change} | Volume Change: {log.volume_change}"
            )

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Transaction rolled back due to: {e}")

    finally:
        db.close()



if __name__ == "__main__":
    run_fraud_batch(user_id=1)
