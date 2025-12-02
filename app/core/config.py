from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "super-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SYNC_DATABASE_URL: str

    OPENAI_API_KEY: str = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = None

    CELERY_BROKER_URL: str = None
    CELERY_RESULT_BACKEND: str = None

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
