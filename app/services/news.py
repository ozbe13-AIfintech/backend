import os
import requests
from datetime import datetime
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"

# 인기 주식 뉴스
def fetch_popular_stock_news(limit: int = 10):
    params = {
        "category": "business",
        "language": "ko",
        "pageSize": limit,
        "apiKey": NEWS_API_KEY,
        "q": "주식 OR 증시 OR 코스피 OR 코스닥"
    }

    res = requests.get(NEWS_API_URL, params=params)
    if res.status_code != 200:
        raise HTTPException(500, "뉴스 API 요청 실패")

    articles = res.json().get("articles", [])
    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "source": a.get("source", {}).get("name"),
            "url": a.get("url"),
            "published_at": datetime.fromisoformat(a.get("publishedAt").replace("Z", "+00:00"))
        }
        for a in articles
    ]

# 뉴스 검색
def search_stock_news(query: str, limit: int = 10):
    params = {
        "q": query,
        "language": "ko",
        "pageSize": limit,
        "apiKey": NEWS_API_KEY
    }

    res = requests.get("https://newsapi.org/v2/everything", params=params)
    if res.status_code != 200:
        raise HTTPException(500, "뉴스 API 요청 실패")

    articles = res.json().get("articles", [])
    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "source": a.get("source", {}).get("name"),
            "url": a.get("url"),
            "published_at": datetime.fromisoformat(a.get("publishedAt").replace("Z", "+00:00"))
        }
        for a in articles
    ]
