from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.mbti import QuestionBase, AnswerRequest
from app.services.mbti import get_next_question, submit_answer, get_mbti_result

router = APIRouter()


# 질문 가져오기 (answered_ids 전달)
@router.get("/question", response_model=QuestionBase)
def next_question(answered_ids: list[int] = Query([]), db: Session = Depends(get_db)):
    q = get_next_question(db, answered_ids)
    if not q:
        raise HTTPException(404, "모든 질문을 완료했습니다.")
    return q


# 답 제출
@router.post("/answer")
def answer(request: AnswerRequest, db: Session = Depends(get_db)):
    submit_answer(db, request.user_id, request.question_id, request.choice)
    return {"message": "answer saved"}


# 결과
@router.get("/result")
def result(user_id: int, db: Session = Depends(get_db)):
    data = get_mbti_result(db, user_id)
    if not data:
        raise HTTPException(404, "MBTI 결과가 없습니다.")
    return data
