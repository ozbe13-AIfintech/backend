from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.mbti import MbtiQuestion

# --- MBTI 질문 데이터 ---
QUESTIONS = [
    # --- E/I ---
    ("E/I", "너는 주식 관련 새로운 정보가 등장하면 어떤 반응을 보이냐?",
     "새 종목 나오면 단톡방에 먼저 공유함",
     "일단 조용히 HTS 열고 1분봉부터 본다"),
    ("E/I", "주식 커뮤니티에서 너의 태도는 어떤 편이냐?",
     "주식방에서 떠드는 게 반쯤 취미다",
     "주식방 알림 뜨면 심장도 같이 뜨는 타입이다"),
    ("E/I", "지인이 종목을 추천했을 때 너는 어떻게 반응하냐?",
     "‘오? 왜?’ 하며 관심 생김",
     "‘근거는?’ 모드 들어감"),
    ("E/I", "사람들과 함께 시장 분석하는 것에 대해 어떻게 생각하냐?",
     "사람들과 같이 분석하는 게 좋다",
     "혼자 집중해서 차트 볼 때 행복하다"),
    ("E/I", "라이브 매매 환경에서 너는?",
     "사람들 반응 보며 매매하는 게 재밌다",
     "혼자 조용히 매매하는 게 좋다"),

    # --- S/N ---
    ("S/N", "투자를 시작할 때 너는 무엇을 먼저 보냐?",
     "PBR·PER·실적표 먼저 본다",
     "미래 비전 PPT 보고 설렌다"),
    ("S/N", "종목을 고를 때 무엇을 더 신뢰하냐?",
     "차트 패턴을 보며 판단",
     "‘곧 뜬다’는 감각을 더 믿음"),
    ("S/N", "정보가 없을 때 너는 매수할 수 있나?",
     "정보 없으면 절대 매수 안 함",
     "느낌적 느낌으로 매수할 때 있음"),
    ("S/N", "가능성을 판단할 때 너는?",
     "현실 가능한 시나리오만 믿음",
     "보이지 않는 가능성에서 기회를 찾음"),

    # --- T/F ---
    ("T/F", "손절에 대한 너의 감정은?",
     "그냥 시스템처럼 클릭하고 끝",
     "헤어진 것처럼 하루종일 생각남"),
    ("T/F", "종목을 살 때 무엇이 더 중요한가?",
     "논리가 맞아야 산다",
     "친구의 열정적인 추천도 큰 영향을 줌"),
    ("T/F", "차트를 볼 때 너는?",
     "‘왜?’ 를 찾는 타입",
     "차트 보며 ‘이 종목 불쌍하네…’ 함"),

    # --- J/P ---
    ("J/P", "매매 계획은 어떻게 세우는 편이냐?",
     "엑셀로 정리하고 체크박스도 있음",
     "시장 열리면 느낌대로 움직임"),
    ("J/P", "포트폴리오 관리 방식은?",
     "목적·비중·리스크 적어둠",
     "즉흥적으로 모아진 종목들"),
    ("J/P", "스케줄 기반 매매는 어때?",
     "일정 안 지켜지면 스트레스",
     "장 열리면 느낌대로 탄다"),
]

# --- 질문 DB 삽입 함수 ---
def seed_questions():
    db: Session = SessionLocal()
    for dimension, text, option_a, option_b in QUESTIONS:
        exists = db.query(MbtiQuestion).filter(
            MbtiQuestion.dimension == dimension,
            MbtiQuestion.text == text
        ).first()
        if exists:
            continue  # 이미 존재하면 건너뜀

        q = MbtiQuestion(
            dimension=dimension,
            text=text,
            option_a=option_a,
            option_b=option_b
        )
        db.add(q)

    db.commit()
    db.close()
    print("✅ MBTI 질문 삽입 완료!")

if __name__ == "__main__":
    seed_questions()
