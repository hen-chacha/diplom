FROM python:3.11-slim

# Установка ffmpeg (это база для твоего загрузчика)
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . .

# Установка зависимостей (хорошо, что в requirements всё есть)
RUN pip install --no-cache-dir -r requirements.txt

# ИСКУССТВО: Запускаем через shell, чтобы подхватить порт от Railway
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"
