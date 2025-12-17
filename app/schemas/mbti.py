from pydantic import BaseModel


class QuestionBase(BaseModel):
    id: int
    text: str
    option_a: str
    option_b: str

    class Config:
        orm_mode = True


class AnswerRequest(BaseModel):
    user_id: int
    question_id: int
    choice: str
