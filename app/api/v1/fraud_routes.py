from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.fraud import FraudLog
from app.schemas.fraud import FraudLogResponse
from app.services import stock
from typing import List

router = APIRouter(tags=["Fraud"])


@router.get("/logs/{stock_id}", response_model=List[FraudLogResponse])
def fraud_logs(stock_id: int, db: Session = Depends(get_db)):
    fraud_logs = (
        db.query(FraudLog)
        .filter(FraudLog.stock_id == stock_id)
        .order_by(FraudLog.created_at.desc())
        .all()
    )
    if not fraud_logs:
        raise HTTPException(status_code=404, detail="No fraud logs found")
    return fraud_logs


@router.get("/{stock_id}/fraud")
def stock_fraud(stock_id: int, user_id: int, db: Session = Depends(get_db)):
    fraud_log, risk_level = stock.detect_fraud(db, stock_id, user_id)

    if not fraud_log:
        raise HTTPException(
            status_code=404, detail="Not enough data for fraud detection"
        )

    return {
        "risk_score": fraud_log.risk_score,
        "reason": fraud_log.reason,
        "risk_level": risk_level,
        "created_at": fraud_log.created_at,
    }
