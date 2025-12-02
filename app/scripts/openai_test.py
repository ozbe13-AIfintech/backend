import os
from dotenv import load_dotenv
import openai

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 OPENAI_API_KEY 가져오기
openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key is None:
    raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

# OpenAI API 클라이언트 설정
openai.api_key = openai_api_key

# 예시: OpenAI GPT-4를 사용한 텍스트 생성
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # GPT-3.5 모델 사용
    messages=[{"role": "user", "content": "안녕하세요! 오늘 기분은 어떤가요?"}],
    max_tokens=50,  # 응답의 최대 길이
)


# 응답 내용 출력
print(response["choices"][0]["message"]["content"].strip())
