from app.db.base import Base  # Base = declarative_base()
from app.db.session import engine

# 실제 DB에 테이블 생성
Base.metadata.create_all(bind=engine)
print("✅ 모든 테이블 생성 완료")
