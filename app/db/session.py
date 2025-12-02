from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.SYNC_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)  # 기본값


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
