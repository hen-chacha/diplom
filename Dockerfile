FROM python:3.11-slim

# Установка ffmpeg на уровне системы
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
