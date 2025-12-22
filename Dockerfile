FROM python:3

WORKDIR /usr/src/oibbot

ADD jobs ./jobs

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y nano && apt-get install -y locales nano && \
apt-get clean

RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

ENV LANG=ru_RU.UTF-8
ENV LANGUAGE=ru_RU:ru
ENV LC_ALL=ru_RU.UTF-8
ENV EDITOR=nano

COPY bot.py ./
COPY .env ./

CMD [ "python", "./bot.py" ]