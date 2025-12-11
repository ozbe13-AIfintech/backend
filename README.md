 AI_fintech 🚀📈
---
주식 거래, 실시간 주가 정보, AI 기반 예측, 뉴스/감정 분석, 거래 내역 관리 등 종합적인 주식 관리 및 분석 기능을 제공하는 백엔드 서비스입니다.




---

### 주요기능🛠️

### 1. 사용자 관리 (User) 👤
- 회원가입, 로그인, OTP 인증, 신원 검증
- 프로필 조회 및 수정
- 찜 목록(Wishlist) 관리

### 2. 주식 관리 (Stocks)) 📊
- 주식 조회, 실시간 데이터 삽입/조회
- 종목 그래프 및 예측 데이터 제공
- 리뷰 작성 및 조회
- 상위 상승 종목 조회

### 3. 사기 탐지 (Fraud) ⚠️
- 배치 단위 주식 사기 탐지
- 개별 주식 사기 조회 및 로그 관리

### 4. 지수 관리 (Index) 💹
- 주식 지수 조회, 생성, 수정, 삭제
- 지수 그래프 제공

### 5. 결제 (Payment) 💳
- 입금, 계좌 잔액 조회

### 6. 감정 분석 (Sentiment) 🧠
- 주식 관련 뉴스 감정 수집 및 트렌드 분석

### 7. 거래 (Trades) 💹
- 주식 매수/매도
- 거래 내역 및 보유 주식 조회

### 8. AI 트레이딩 (AI_trading) 🤖
- AI 기반 자동 매매 실행 및 히스토리 조회

### 9. 뉴스 (News) 🗞️
- 인기 뉴스, 주식 뉴스, 검색 뉴스, 최신 뉴스 제공

### 10. 환율 (Forex)  💱
- 환율 조회 및 목록 제공

### 11. 검색 (Search) 🔎 
- 통합 검색 기능

### 12. MBTI 기능 🧩
- 질문/응답 기반 MBTI 설문 및 결과 제공

> ⚡ **모든 엔드포인트 목록은 프로젝트 문서 참고**  

---
#기술 스택🛠️

- **Backend:** FastAPI , Python
- **Database:** PostgreSQL / SQLAlchemy
- **Authentication:** JWT, OTP
- **API 문서화:** Swagger 

---

## 설치 및 실행 💻
```bash
git clone https://github.com/ozbe13-AIfintech/backend.git
cd AI_fintech
python -m venv venv
source .venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
uvicorn main:app --reload
