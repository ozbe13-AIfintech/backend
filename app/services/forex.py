import requests
from datetime import datetime
from fastapi import HTTPException

EXCHANGE_API_URL = "https://api.exchangerate.host/latest"


def get_exchange_rate(base: str, target: str):
    params = {"base": base.upper(), "symbols": target.upper()}
    res = requests.get(EXCHANGE_API_URL, params=params)

    if res.status_code != 200:
        raise HTTPException(500, "환율 API 요청 실패")

    data = res.json()
    if target.upper() not in data.get("rates", {}):
        raise HTTPException(404, "대상 통화를 찾을 수 없음")

    return {
        "base_currency": base.upper(),
        "target_currency": target.upper(),
        "rate": data["rates"][target.upper()],
        "last_updated": datetime.fromisoformat(data["date"]),
    }
