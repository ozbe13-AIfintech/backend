from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

from sqlalchemy import Column, Integer, String
from app.db.base import Base

class MbtiQuestion(Base):
    __tablename__ = "mbti_questions"

    id = Column(Integer, primary_key=True, index=True)
    dimension = Column(String(10), nullable=False)  # ex) "E/I"
    option_a = Column(String, nullable=False)        # EX: 외향적 선택지
    option_b = Column(String, nullable=False)        # IN: 내향적 선택지
    text = Column(String, nullable=False)


class UserMBTI(Base):
    __tablename__ = "user_mbti"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)

    E = Column(Integer, default=0)
    I = Column(Integer, default=0)
    S = Column(Integer, default=0)
    N = Column(Integer, default=0)
    T = Column(Integer, default=0)
    F = Column(Integer, default=0)
    J = Column(Integer, default=0)
    P = Column(Integer, default=0)

    result = Column(String(4), nullable=True)
