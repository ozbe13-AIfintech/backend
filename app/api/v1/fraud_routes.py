from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.schemas.fraud import FraudLogResponse
from app.services.fraud_detector import detect_fraud_service, detect_multiple_fraud_service, determine_risk_level
from app.models.stock import Stock
from app.core.security import get_current_user  # JWT 인증
from app.models.fraud import FraudLog

router = APIRouter(tags=["Fraud"])

# ---------------- 배치 탐지 (이미 구현) ----------------
@router.get("/fraud/batch", response_model=List[FraudLogResponse])
def batch_stock_fraud(
    stock_ids: Optional[List[int]] = Query(None, description="List of stock IDs (optional)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    if stock_ids is None:
        stock_ids = [s.id for s in db.query(Stock).all()]

    fraud_logs = detect_multiple_fraud_service(db, stock_ids, user_id)

    if not fraud_logs:
        raise HTTPException(status_code=404, detail="Not enough data for fraud detection")

    return [
        {
            "user_id": log.user_id,
            "stock_id": log.stock_id,
            "risk_score": log.risk_score,
            "reason": log.reason,
            "price_change": log.price_change,
            "volume_change": log.volume_change,
            "average_price": log.average_price,
            "average_volume": log.average_volume,
            "risk_level": determine_risk_level(log.risk_score),
            "created_at": log.created_at,
        }
        for log in fraud_logs
    ]

# ⚠ 반드시 /fraud/logs 가 /fraud/{stock_id}보다 위에 있어야 함
@router.get("/fraud/logs", response_model=List[FraudLogResponse])
def get_fraud_logs(
    stock_id: Optional[int] = Query(None, description="Optional stock ID to filter logs"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(FraudLog).filter(FraudLog.user_id == current_user.id)
    if stock_id:
        query = query.filter(FraudLog.stock_id == stock_id)

    logs = query.order_by(FraudLog.created_at.desc()).all()
    if not logs:
        raise HTTPException(status_code=404, detail="No fraud logs found")

    return [
        {
            "user_id": log.user_id,
            "stock_id": log.stock_id,
            "risk_score": log.risk_score,
            "reason": log.reason,
            "price_change": log.price_change,
            "volume_change": log.volume_change,
            "average_price": log.average_price,
            "average_volume": log.average_volume,
            "risk_level": determine_risk_level(log.risk_score),
            "created_at": log.created_at,
        }
        for log in logs
    ]

# ---------------- 개별 주식 단일 탐지 ----------------
@router.get("/fraud/{stock_id}", response_model=FraudLogResponse)
def single_stock_fraud(
    stock_id: int = Path(..., description="ID of the stock to check fraud"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_id = current_user.id
    fraud_log, risk_level = detect_fraud_service(db, stock_id, user_id)

    if not fraud_log:
        raise HTTPException(status_code=404, detail="Not enough data for fraud detection")

    return {
        "user_id": fraud_log.user_id,
        "stock_id": fraud_log.stock_id,
        "risk_score": fraud_log.risk_score,
        "reason": fraud_log.reason,
        "price_change": fraud_log.price_change,
        "volume_change": fraud_log.volume_change,
        "average_price": fraud_log.average_price,
        "average_volume": fraud_log.average_volume,
        "risk_level": determine_risk_level(fraud_log.risk_score),
        "created_at": fraud_log.created_at,
    }


