from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from app.schemas.trade import OwnedStockResponse
from app.models.trade import Trade, UserAsset
from app.models.user import User
from app.models.stock import Stock, StockPrice
from sqlalchemy import func


def buy_stock(db: Session, user_id: int, stock_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="주문 수량은 1 이상이어야 합니다.")

    user = db.query(User).filter(User.id == user_id).first()
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not user or not stock:
        raise HTTPException(
            status_code=404, detail="사용자 또는 주식이 존재하지 않습니다."
        )


    latest_price_record = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at.desc())
        .first()
    )
    if not latest_price_record:
        raise HTTPException(status_code=500, detail="주식 가격 정보가 없습니다.")

    price = latest_price_record.price
    total_price = price * quantity

    if user.balance < total_price:
        raise HTTPException(status_code=400, detail="잔액이 부족합니다.")

    try:

        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            price=price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )
        db.add(trade)


        asset = (
            db.query(UserAsset).filter_by(user_id=user_id, stock_id=stock_id).first()
        )
        if asset:
            asset.avg_price = (asset.quantity * asset.avg_price + quantity * price) / (
                asset.quantity + quantity
            )
            asset.quantity += quantity
        else:
            asset = UserAsset(
                user_id=user_id, stock_id=stock_id, quantity=quantity, avg_price=price
            )
            db.add(asset)

        user.balance -= total_price

        db.commit()
        db.refresh(trade)
        return trade
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"구매 실패: {str(e)}")


def sell_stock(db: Session, user_id: int, stock_id: int, quantity: int):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="판매 수량은 1 이상이어야 합니다.")

    user = db.query(User).filter(User.id == user_id).first()
    asset = db.query(UserAsset).filter_by(user_id=user_id, stock_id=stock_id).first()
    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    if not user or not stock or not asset:
        raise HTTPException(
            status_code=404, detail="사용자, 주식, 또는 자산이 존재하지 않습니다."
        )

    if asset.quantity < quantity:
        raise HTTPException(status_code=400, detail="보유 수량이 부족합니다.")


    latest_price_record = (
        db.query(StockPrice)
        .filter(StockPrice.stock_id == stock_id)
        .order_by(StockPrice.recorded_at.desc())
        .first()
    )
    if not latest_price_record:
        raise HTTPException(status_code=500, detail="주식 가격 정보가 없습니다.")

    price = latest_price_record.price
    total_price = price * quantity

    try:

        trade = Trade(
            user_id=user_id,
            stock_id=stock_id,
            quantity=-quantity,
            price=price,
            total_price=total_price,
            created_at=datetime.utcnow(),
        )
        db.add(trade)


        asset.quantity -= quantity
        if asset.quantity == 0:
            db.delete(asset)

        user.balance += total_price

        db.commit()
        db.refresh(trade)
        return trade
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"판매 실패: {str(e)}")


def get_user_trades(db: Session, user_id: int):
    return (
        db.query(Trade)
        .filter(Trade.user_id == user_id)
        .order_by(Trade.created_at.desc())
        .all()
    )


def get_user_owned_stocks(db: Session, user_id: int) -> list[OwnedStockResponse]:
    """
    JWT 인증된 사용자의 보유 주식 조회
    """

    trades = (
        db.query(
            Trade.stock_id,
            func.sum(Trade.quantity).label("total_quantity"),
            func.avg(Trade.price).label("avg_price"),
        )
        .filter(Trade.user_id == user_id)
        .group_by(Trade.stock_id)
        .all()
    )

    owned_stocks: list[OwnedStockResponse] = []

    for t in trades:
        if t.total_quantity <= 0:
            continue

        stock = db.query(Stock).filter(Stock.id == t.stock_id).first()
        if not stock:
            continue


        latest_price_obj = StockPrice.get_latest_price(db, stock_id=t.stock_id)
        current_price = latest_price_obj.price if latest_price_obj else 0.0

        owned_stocks.append(
            OwnedStockResponse(
                id=stock.id,
                name=stock.name,
                symbol=stock.symbol,
                quantity=int(t.total_quantity),
                avg_price=float(t.avg_price),
                current_price=current_price,
            )
        )

    return owned_stocks
