import requests
from datetime import datetime
from fastapi import HTTPException
from app.models.forex import ExchangeRate, ExchangeRateHistory
from sqlalchemy.orm import Session

EXCHANGE_API_URL = "https://api.frankfurter.app/latest"
print("EXCHANGE_API_URL =", EXCHANGE_API_URL)

def get_multiple_exchange_rates(base: str, targets: list, db: Session):
    symbols = ",".join([t.upper() for t in targets])
    url = f"{EXCHANGE_API_URL}?from={base.upper()}&to={symbols}"
    print("호출 URL 확인:", url)

    res = requests.get(url)
    if res.status_code != 200:
        raise HTTPException(500, "환율 API 요청 실패")

    data = res.json()
    if "rates" not in data:
        raise HTTPException(500, f"API 응답에 'rates' 없음: {data}")

    last_updated = datetime.utcnow()
    results = []

    for target, rate in data["rates"].items():
        record = db.query(ExchangeRate).filter(
            ExchangeRate.base_currency == base.upper(),
            ExchangeRate.target_currency == target.upper()
        ).first()
        if record:
            record.rate = rate
            record.last_updated = last_updated
            record.source = "frankfurter.app"
        else:
            record = ExchangeRate(
                base_currency=base.upper(),
                target_currency=target.upper(),
                rate=rate,
                last_updated=last_updated,
                source="frankfurter.app"
            )
            db.add(record)

        history = ExchangeRateHistory(
            base_currency=base.upper(),
            target_currency=target.upper(),
            rate=rate
        )
        db.add(history)

        results.append({
            "base_currency": base.upper(),
            "target_currency": target.upper(),
            "rate": rate,
            "last_updated": last_updated,
            "source": "frankfurter.app"
        })

    db.commit()
    return results

def get_exchange_rate(base: str, target: str, db: Session):
    return get_multiple_exchange_rates(base, [target], db)[0]
