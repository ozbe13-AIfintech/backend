
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "super-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str
    SYNC_DATABASE_URL: str = None

    OPENAI_API_KEY: str = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CELERY_BROKER_URL: str = None
    CELERY_RESULT_BACKEND: str = None

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }


settings = Settings()
