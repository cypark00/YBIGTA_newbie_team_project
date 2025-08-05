# 1. Python 이미지 기반
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성만 먼저 복사
COPY requirements-prod.txt .

# 4. 패키지 먼저 설치
RUN pip install --no-cache-dir -r requirements-prod.txt

# 5. 나머지 코드 복사
COPY . .

# 6. 포트 열기
EXPOSE 8000

# 7. 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]