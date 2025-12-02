import requests
from datetime import datetime
from fastapi import HTTPException
from app.models.forex import ExchangeRate, ExchangeRateHistory
from app.db.session import SessionLocal
from sqlalchemy.orm import Session

EXCHANGE_API_URL = "https://api.exchangerate.host/convert"
API_KEY = "b44607f2b18ab5d41596606c34d25c66"  # 발급받은 API 키

def get_exchange_rate(base: str, target: str, db: Session):
    params = {
        "from": base.upper(),
        "to": target.upper(),
        "amount": 1,  # 변환할 금액 (예: 1 USD)
        "access_key": API_KEY  # API 키를 URL 파라미터로 추가
    }

    # 요청 보내기
    res = requests.get(EXCHANGE_API_URL, params=params)

    # 응답 상태 코드 체크
    if res.status_code != 200:
        raise HTTPException(500, "환율 API 요청 실패")

    data = res.json()

    # API 응답에서 대상 통화가 없을 경우
    if "result" not in data:
        raise HTTPException(404, "대상 통화를 찾을 수 없음")

    rate = data["result"]
    last_updated = datetime.utcnow()  # `convert` API는 실시간이라 마지막 업데이트는 현재 시간으로 처리

    # 환율 정보를 DB에 저장
    exchange_rate = ExchangeRate(
        base_currency=base.upper(),
        target_currency=target.upper(),
        rate=rate,
        last_updated=last_updated,
        source="exchangerate.host"
    )

    db.add(exchange_rate)
    db.commit()

    # 환율 히스토리 저장
    exchange_rate_history = ExchangeRateHistory(
        base_currency=base.upper(),
        target_currency=target.upper(),
        rate=rate,
    )

    db.add(exchange_rate_history)
    db.commit()

    # 환율 데이터 반환
    return {
        "base_currency": base.upper(),
        "target_currency": target.upper(),
        "rate": rate,
        "last_updated": last_updated,
        "source": "exchangerate.host",
    }
