FROM python:3.11-slim

# Установка ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Просто запускаем скрипт, он сам разберется с портом
CMD ["python", "main.py"]
