from datetime import datetime, timedelta
import ssl
import sqlite3
import json
import logging

import aiohttp
import os

import requests.exceptions
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from telegram.ext import CallbackContext
from dotenv import load_dotenv

logging.basicConfig(level=logging.WARNING, filename="jobs/data/logs.log", filemode="a")

load_dotenv()
CHAT_ID = os.getenv('CHAT_ID')

# обязательно нужно подделывать поле User-Agent, иначе onco.tnimc.ru и tnimc.ru не пустят к себе
HEADERS = {
    'Accept': "text/html",
    'User-Agent': UserAgent().random
}


async def check_sites(context: CallbackContext) -> None:
    '''
    Для проверки веб-ресурсов, указанных в словарь URLS, на целостность.
    Проверка осуществляется по заранее выбранным элементам DOM-структуры и сохраненным
    в словарь URLS.
    :param context: CallbackContext
    :return: None
    '''

    urls = from_json("jobs/data/urls.json")
    failed_checks = [] # записывается информация о каждой неудачной проверке каждого сайта
    text = '' # текст для записи в БД
    check_result = True # флаг для отслеживания результата проверки и записи в БД

    async with aiohttp.ClientSession() as session:
        for name in urls.keys():
            try:
                url = urls.get(name).get('url')

                async with session.get(url, headers=HEADERS, ssl=False) as response:
                    response.raise_for_status()
                    html_page = await response.text()

                    soup = BeautifulSoup(html_page, 'lxml')
                    result = soup.select(urls.get(name).get('css-selector')[0])

                    if len(result) > 0:
                        if str(result[0]) != urls.get(name).get('css-selector')[1]:
                            failed_checks.append(f'{url} -> Элемент не найден;')
                    else:
                        failed_checks.append(f'{url} -> Элемент не найден;')

            except aiohttp.ClientError as http_error:
                http_error = str(http_error)

                failed_checks.append(f'{url} -> {http_error};')

            except ssl.SSLCertVerificationError:
                failed_checks.append(f'{url} -> Проверка SSL сертификата завершилась неудачно.;')

            except Exception as error:
                error = str(error)

                failed_checks.append(f'{url} -> {error};')

    time_now = datetime.now() + timedelta(hours=7)

    if len(failed_checks) == 0:
        text = 'Веб-ресурсы успешно прошли проверки'
    else:
        check_result = False
        for el in failed_checks:
            text += str(el)

    with sqlite3.connect('jobs/data/check_info_sites.db') as connection:
        cursor = connection.cursor()

        try:
            with connection:
                query = "INSERT INTO Checks (result, text, create_time) VALUES (?, ?, ?)"
                cursor.execute(query,(check_result, text, time_now))

        except Exception as ex:
            logging.warning(f"{str(ex)}")


async def send_notifications_for_sites_checking(context: CallbackContext) -> None:
    '''
    Для отправки уведомлений в групповой чат о
    состояниях прошедших проверок.
    :param context: CallbackContext
    :return: None
    '''
    time_day_ago = datetime.now() + timedelta(hours=7) - timedelta(hours=24)
    query_result = []

    with sqlite3.connect('jobs/data/check_info_sites.db') as connection:
        cursor = connection.cursor()

        try:
            with connection:
                # выборка из БД проверок, проведенных за последние 24 часа, начиная с отправки уведомления
                query = '''
                SELECT * FROM Checks
                WHERE create_time >= ?
                '''

                cursor.execute(query, (time_day_ago,))
                query_result = cursor.fetchall()

        except Exception as ex:
            logging.warning(f"{str(ex)}")

    checks_results = []

    for row in query_result:
        checks_results.append(bool(row[1]))

    overall_result = all(checks_results)

    count_of_checks = len(query_result)
    time_of_checks = [row[3] for row in query_result]
    time_of_checks_str = ''

    for index in range(len(time_of_checks)):
        time_of_checks_str += f"{str(index + 1)}. {time_of_checks[index][:-7]}\n"

    if overall_result:
        text = (f"Количество проверок: {count_of_checks}\n"
                f"Время проверок:\n{time_of_checks_str}\n"
                f"Результат: ✅")

        await context.bot.send_message(chat_id=CHAT_ID, text=text)
    else:
        warnings = 0
        check_result_str = ''

        for row in query_result:
            if bool(row[1]) is False:
                warnings += 1

        for index in range(len(query_result)):
            if bool(query_result[index][1]) is False:
                # строка такого формата на входе https://инфарктанет.рф/ -> list index out of range;
                # https://finfarktanet.ru/ -> Cannot connect to host finfarktanet.ru:443 ssl:False [getaddrinfo failed];
                # https://tnimc.ru/ -> Элемент не найден;
                prep_check_result = query_result[index][2].split(';')[:-1]
                prev_str = f'Проверка {str(index + 1)}: ❌\n'

                check_result_str += prev_str

                for jndex in range(len(prep_check_result)):
                    check_result_str += f"{str(jndex + 1)}. {prep_check_result[jndex]}\n"

        text = (f"Количество проверок: {count_of_checks}\n"
                f"Количество успешных проверок: {count_of_checks - warnings}\n"
                f"Время проверок:\n{time_of_checks_str}\n"
                f"Результат:\n{check_result_str}")

        await context.bot.send_message(chat_id=CHAT_ID, text=text, disable_web_page_preview=True)


def from_json(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as urls:
        data = json.load(urls)
    return data
