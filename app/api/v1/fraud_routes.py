from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.services.fraud_detector import (
    detect_fraud_service,
    detect_multiple_fraud_service,
    get_fraud_logs_service,
    determine_risk_level,
)
from app.models.stock import Stock
from app.models.fraud import FraudLog
from app.core.security import get_current_user
from app.schemas.fraud import FraudLogResponse

router = APIRouter()

@router.post("/batch", response_model=List[FraudLogResponse])
def batch_stock_fraud(
    stock_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fraud_logs = detect_multiple_fraud_service(db, stock_ids, current_user.id)

    if not fraud_logs:
        raise HTTPException(status_code=404, detail="Not enough data for fraud detection")

    results = []
    for log in fraud_logs:
        stock = db.query(Stock).filter(Stock.id == log.stock_id).first()
        results.append({
            "user_id": log.user_id,
            "stock_id": log.stock_id,
            "stock_name": stock.name if stock else "",
            "stock_symbol": stock.symbol if stock else "",
            "risk_score": log.risk_score,
            "reason": log.reason,
            "price_change": log.price_change,
            "volume_change": log.volume_change,
            "average_price": log.average_price,
            "average_volume": log.average_volume,
            "risk_level": determine_risk_level(log.risk_score),
            "created_at": log.created_at,
        })

    return results


@router.get("/logs", response_model=List[FraudLogResponse])
def get_fraud_logs(
    stock_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    logs = get_fraud_logs_service(db, stock_id)
    logs = [log for log in logs if log.user_id == current_user.id]

    if not logs:
        raise HTTPException(status_code=404, detail="No fraud logs found")

    results = []
    for log in logs:
        stock = db.query(Stock).filter(Stock.id == log.stock_id).first()
        results.append({
            "user_id": log.user_id,
            "stock_id": log.stock_id,
            "stock_name": stock.name if stock else "",
            "stock_symbol": stock.symbol if stock else "",
            "risk_score": log.risk_score,
            "reason": log.reason,
            "price_change": log.price_change,
            "volume_change": log.volume_change,
            "average_price": log.average_price,
            "average_volume": log.average_volume,
            "risk_level": determine_risk_level(log.risk_score),
            "created_at": log.created_at,
        })

    return results


@router.get("/{stock_id}", response_model=FraudLogResponse)
def single_stock_fraud(
    stock_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fraud_log, _ = detect_fraud_service(db, stock_id, current_user.id)

    if not fraud_log:
        raise HTTPException(status_code=404, detail="Not enough data for fraud detection")

    stock = db.query(Stock).filter(Stock.id == fraud_log.stock_id).first()

    return {
        "user_id": fraud_log.user_id,
        "stock_id": fraud_log.stock_id,
        "stock_name": stock.name if stock else "",
        "stock_symbol": stock.symbol if stock else "",
        "risk_score": fraud_log.risk_score,
        "reason": fraud_log.reason,
        "price_change": fraud_log.price_change,
        "volume_change": fraud_log.volume_change,
        "average_price": fraud_log.average_price,
        "average_volume": fraud_log.average_volume,
        "risk_level": determine_risk_level(fraud_log.risk_score),
        "created_at": fraud_log.created_at,
    }
