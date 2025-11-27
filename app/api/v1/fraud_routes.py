from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.fraud import FraudLogResponse
from app.services.fraud_service import get_fraud_logs_service, detect_fraud_service

router = APIRouter(tags=["Fraud"])

@router.get("/logs/{stock_id}", response_model=List[FraudLogResponse])
def fraud_logs(stock_id: int, db: Session = Depends(get_db)):
    logs = get_fraud_logs_service(db, stock_id)
    if not logs:
        raise HTTPException(status_code=404, detail="No fraud logs found")
    return logs


@router.get("/{stock_id}/fraud")
def stock_fraud(stock_id: int, user_id: int, db: Session = Depends(get_db)):
    fraud_log, risk_level = detect_fraud_service(db, stock_id, user_id)
    if not fraud_log:
        raise HTTPException(status_code=404, detail="Not enough data for fraud detection")
    return {
        "risk_score": fraud_log.risk_score,
        "reason": fraud_log.reason,
        "risk_level": risk_level,
        "created_at": fraud_log.created_at,
    }
