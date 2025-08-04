# 1. Python 이미지 기반
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 현재 프로젝트 코드 복사
COPY . /app

# 4. 패키지 설치
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 5. 포트 열기
EXPOSE 8000

# 6. 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]