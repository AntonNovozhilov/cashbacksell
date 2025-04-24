# Базовый образ Python
FROM python:3.11-slim

# Установка рабочих зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копирование зависимостей
COPY req.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r req.txt

# Копирование исходного кода бота
COPY . .

# Старт бота
CMD ["python", "botmessage copy.py"]
