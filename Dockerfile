FROM python:3.13-alpine

WORKDIR /usr/src/oibbot

# Устанавливаем только необходимые пакеты
RUN apk add --no-cache nano

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EDITOR=nano \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Устанавливаем Python зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
ADD jobs ./jobs
COPY bot.py ./
COPY .env ./

# Запускаем приложение
CMD ["python", "./bot.py"]
