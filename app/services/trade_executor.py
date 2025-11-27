from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

from app.models.trade import Trade
from app.models.user import User
from app.models.stock import Stock


def create_trade(db: Session, user_id: int, stock_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="주문 수량은 1 이상이어야 합니다.")

    user = db.query(User).filter(User.id == user_id).first()
    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if not stock:
        raise HTTPException(status_code=404, detail="주식을 찾을 수 없습니다.")

    if stock.current_price is None:
        raise HTTPException(500, detail="주식 가격 정보가 없습니다.")

    total_price = stock.current_price * quantity

    # 잔액 체크
    if getattr(user, "balance", 0) < total_price:
        raise HTTPException(status_code=400, detail="잔액이 부족합니다.")

    try:
        # 거래 생성
        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            price=stock.current_price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )

        db.add(trade)
        user.balance -= total_price

        db.commit()
        db.refresh(trade)

        return trade

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"거래 실패: {str(e)}")


def get_user_trades(db: Session, user_id: int):
    return (
        db.query(Trade)
        .filter(Trade.user_id == user_id)
        .order_by(Trade.created_at.desc())
        .all()
    )
