from sqlalchemy.orm import Session
from datetime import datetime
from app.models.trade import Trade
from app.models.user import User
from app.models.stock import Stock


def create_trade(db: Session, user_id: int, stock_id: int, quantity: int):
    if quantity <= 0:
        raise ValueError("주문 수량은 1 이상이어야 합니다.")

    user = db.query(User).filter(User.id == user_id).first()
    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    if not user or not stock:
        raise ValueError("사용자 또는 주식을 찾을 수 없습니다.")

    total_price = stock.current_price * quantity

    # 잔액 체크
    if getattr(user, "balance", 0) < total_price:
        raise ValueError("잔액이 부족합니다.")

    try:
        # 트랜잭션 시작
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
        raise e


def get_user_trades(db: Session, user_id: int):
    return (
        db.query(Trade)
        .filter(Trade.user_id == user_id)
        .order_by(Trade.created_at.desc())
        .all()
    )
