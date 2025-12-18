from app.db.base import Base
from app.db.session import engine

try:
    Base.metadata.create_all(bind=engine)
    print("✅ 모든 테이블 생성 완료")
except Exception as e:
    print("테이블 생성 중 오류 발생:", e)
