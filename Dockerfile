FROM python:3.13-alpine

WORKDIR /usr/src/oibbot

RUN apk add --no-cache nano

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EDITOR=nano \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EDITOR=nano \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ADD jobs ./jobs
COPY bot.py ./
COPY .env ./

CMD ["python", "./bot.py"]
