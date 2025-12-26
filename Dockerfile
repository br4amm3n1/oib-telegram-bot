FROM python:3.13-alpine

WORKDIR /usr/src/oibbot

<<<<<<< HEAD
# Устанавливаем только необходимые пакеты
RUN apk add --no-cache nano
=======
RUN apk add --no-cache nano

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EDITOR=nano \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
>>>>>>> 07e94512f1a0c996e7db12ccdb17b1ada06203b1

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

<<<<<<< HEAD
# Копируем исходный код
=======
>>>>>>> 07e94512f1a0c996e7db12ccdb17b1ada06203b1
ADD jobs ./jobs
COPY bot.py ./
COPY .env ./

<<<<<<< HEAD
# Запускаем приложение
CMD ["python", "./bot.py"]
=======
CMD ["python", "./bot.py"]
>>>>>>> 07e94512f1a0c996e7db12ccdb17b1ada06203b1
