from sys import prefix
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.api.v1 import user_routes
from app.api.v1 import stock_routes
from app.api.v1 import fraud_routes
from app.api.v1 import index_routes
from app.api.v1 import payment_routes
from app.api.v1 import sentiment_routes
from app.api.v1 import trade_routes
from app.api.v1.ai_trading_routes import router as ai_trading_routes
from app.api.v1 import news
from app.api.v1 import forex
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI FinTech API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(stock_routes.router, prefix="/api/v1/stocks", tags=["Stocks"])
app.include_router(fraud_routes.router, prefix="/api/v1/fraud", tags=["Fraud"])
app.include_router(index_routes.router, prefix="/api/v1/index", tags=["Index"])
app.include_router(payment_routes.router, prefix="/api/v1/payment", tags=["Payment"])
app.include_router(
    sentiment_routes.router, prefix="/api/v1/sentiment", tags=["Sentiment"]
)
app.include_router(trade_routes.router, prefix="/api/v1/trades", tags=["Trades"])
app.include_router(ai_trading_routes)
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(forex.router, prefix="/api/v1/forex", tags=["Forex"])


@app.get("/")
def root():
    return {"message": "Hello AI FinTech!"}
