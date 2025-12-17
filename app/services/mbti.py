from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.mbti import MbtiQuestion, UserMBTI
import random
from typing import List, Optional



def get_next_question(
    db: Session, answered_ids: Optional[List[int]] = None
) -> Optional[MbtiQuestion]:
    if answered_ids is None:
        answered_ids = []
    questions = db.query(MbtiQuestion).filter(~MbtiQuestion.id.in_(answered_ids)).all()
    if not questions:
        return None
    return random.choice(questions)



def submit_answer(db: Session, user_id: int, question_id: int, choice: str):
    question = db.query(MbtiQuestion).filter(MbtiQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="존재하지 않는 질문입니다.")


    user_mbti = db.query(UserMBTI).filter(UserMBTI.user_id == user_id).first()
    if not user_mbti:
        user_mbti = UserMBTI(user_id=user_id)
        db.add(user_mbti)
        db.commit()
        db.refresh(user_mbti)


    dim_map = {
        "E/I": ("E", "I"),
        "S/N": ("S", "N"),
        "T/F": ("T", "F"),
        "J/P": ("J", "P"),
    }
    if question.dimension not in dim_map:
        raise HTTPException(status_code=400, detail="잘못된 dimension")

    col = (
        dim_map[question.dimension][0]
        if choice.upper() == "A"
        else dim_map[question.dimension][1]
    )
    setattr(user_mbti, col, getattr(user_mbti, col) + 1)
    db.commit()



def calc_mbti(user_mbti: UserMBTI) -> str:
    result = ""
    result += "E" if user_mbti.E >= user_mbti.I else "I"
    result += "S" if user_mbti.S >= user_mbti.N else "N"
    result += "T" if user_mbti.T >= user_mbti.F else "F"
    result += "J" if user_mbti.J >= user_mbti.P else "P"
    return result



def get_mbti_result(db: Session, user_id: int):
    user = db.query(UserMBTI).filter(UserMBTI.user_id == user_id).first()
    if not user:
        return None

    result = calc_mbti(user)
    user.result = result
    db.commit()
    db.refresh(user)

    recommendations = {
        "ISTJ": {
            "stocks": ["삼성전자", "SK하이닉스"],
            "etf": ["TIGER 200"],
            "desc": "철저한 분석형. 안정적 투자.",
        },
        "ISFJ": {
            "stocks": ["LG생활건강", "CJ제일제당"],
            "etf": ["KODEX 배당"],
            "desc": "조용하지만 꾸준한 수익형.",
        },
        "INFJ": {
            "stocks": ["네이버", "카카오"],
            "etf": ["TIGER 콘텐츠"],
            "desc": "트렌드를 깊게 이해하는 스타일.",
        },
        "INTJ": {
            "stocks": ["엔비디아", "ASML"],
            "etf": ["SOXX"],
            "desc": "미래기술 투자자.",
        },
        "ISTP": {
            "stocks": ["현대모비스", "한국항공우주"],
            "etf": ["기계장비 ETF"],
            "desc": "실전형 투자자.",
        },
        "ISFP": {
            "stocks": ["아모레", "F&F"],
            "etf": ["소비재 ETF"],
            "desc": "감각적 트렌드 투자.",
        },
        "INFP": {
            "stocks": ["펄어비스", "하이브"],
            "etf": ["KPOP ETF"],
            "desc": "논리는 갖다 팔아 버린 유동성.",
        },
        "INTP": {
            "stocks": ["퀄컴", "삼성SDI"],
            "etf": ["2차전지 ETF"],
            "desc": "이론 분석형 투자자.",
        },
        "ESTP": {
            "stocks": ["포스코퓨처엠", "L&F"],
            "etf": ["KODEX 레버리지"],
            "desc": "단타·상승장 강함.",
        },
        "ESFP": {
            "stocks": ["카카오게임즈", "JYP"],
            "etf": ["엔터 ETF"],
            "desc": "재미 중시 투자.",
        },
        "ENFP": {
            "stocks": ["테슬라", "루시드"],
            "etf": ["ARKK"],
            "desc": "혁신 미래 열정형.",
        },
        "ENTP": {
            "stocks": ["엔비디아", "슈퍼마이크로"],
            "etf": ["SOXL"],
            "desc": "기회 포착형.",
        },
        "ESTJ": {
            "stocks": ["삼성전자", "현대차"],
            "etf": ["KODEX 200"],
            "desc": "대장주 안정형.",
        },
        "ESFJ": {
            "stocks": ["CJ ENM", "롯데칠성"],
            "etf": ["소비재 ETF"],
            "desc": "분위기·커뮤니티 반영.",
        },
        "ENFJ": {
            "stocks": ["애플", "MSFT"],
            "etf": ["QQQ"],
            "desc": "장기적 비전 투자.",
        },
        "ENTJ": {
            "stocks": ["아마존", "메타"],
            "etf": ["SPY"],
            "desc": "전략적 빅테크 투자.",
        },
    }

    return {
        "mbti": result,
        "description": recommendations[result]["desc"],
        "recommended_stocks": recommendations[result]["stocks"],
        "recommended_etf": recommendations[result]["etf"],
    }
