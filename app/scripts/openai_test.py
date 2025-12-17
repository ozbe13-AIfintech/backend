import os
from dotenv import load_dotenv
import openai


load_dotenv()


openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key is None:
    raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")


openai.api_key = openai_api_key


response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "안녕하세요! 오늘 기분은 어떤가요?"}],
    max_tokens=50,
)



print(response["choices"][0]["message"]["content"].strip())
