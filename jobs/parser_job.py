from datetime import datetime, timedelta
import ssl
import sqlite3
import json
import logging

import aiohttp
import asyncio
import os

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


def format_datetime_for_db(dt: datetime) -> str:
    """Форматирует datetime в строку для SQLite"""
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:26]


async def check_free_vps(context: CallbackContext) -> None:
    '''
    Для проверки наличия доступных для покупки VPS серверов на
    weasel.cloud.
    :param context: CallbackContext
    :return: None
    '''

    urls = from_json("jobs/data/urls_vps.json")

    async def check_one_vps_country(site_name: str) -> None:
        url = urls.get(site_name).get('url')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS) as response:
                    response.encoding = 'utf-8'
                    html_page = await response.text()

                    css_selectors = urls.get(site_name).get('css-selectors')

                    soup = BeautifulSoup(html_page, 'lxml')

                    for css_selector in css_selectors:
                        result = soup.select(css_selector[1])

                        inline_text = result[0].get_text(strip=True)
                        free_count = inline_text[:inline_text.index(' ')]

                        text = "На %s появились доступные 🖥 VPS (%s) в количестве %s шт." % (url, css_selector[0], free_count)

                        if int(free_count) > 0:
                            await context.bot.send_message(chat_id=CHAT_ID, text=text, disable_web_page_preview=True)
        except Exception as ex:
            logging.warning(f"{str(ex)}")

    await asyncio.gather(*[check_one_vps_country(name) for name in urls.keys()])

async def check_sites(context: CallbackContext) -> None:
    '''
    Для проверки веб-ресурсов, указанных в словарь URLS, на целостность.
    Проверка осуществляется по заранее выбранным элементам и сохраненным
    в словарь URLS.
    :param context: CallbackContext
    :return: None
    '''

    urls = from_json("jobs/data/urls.json")
    failed_checks = [] # записывается информация о каждой неудачной проверке каждого сайта
    text = '' # текст для записи в БД
    check_result = True # флаг для отслеживания результата проверки и записи в БД

    async def check_one_site(site_name: str) -> None:
        url = urls.get(site_name).get('url')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADERS, ssl=False) as response:
                    response.raise_for_status()
                    html_page = await response.text()

                    soup = BeautifulSoup(html_page, 'lxml')
                    result = soup.select(urls.get(site_name).get('css-selector')[0])

                    if len(result) > 0:
                        if str(result[0]) != urls.get(site_name).get('css-selector')[1]:
                            failed_checks.append(f'{url} -> Элемент не найден;')
                    else:
                        failed_checks.append(f'{url} -> Элемент не найден;')

        except aiohttp.ClientError as http_error:
            http_error = str(http_error)

            failed_checks.append(f'{url} -> {http_error};')

        except ssl.SSLCertVerificationError:
            failed_checks.append(f'{url} -> Проверка SSL сертификата завершилась неудачно.;')

    await asyncio.gather(*[check_one_site(name) for name in urls.keys()])

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
    time_day_ago = datetime.now() + timedelta(hours=7) - timedelta(hours=4)
    time_for_db = format_datetime_for_db(time_day_ago)
    query_result: tuple

    with sqlite3.connect('jobs/data/check_info_sites.db') as connection:
        cursor = connection.cursor()

        try:
            with connection:
                # выборка из БД провальной проверки, проведенной за последние 4 часа
                query = '''
                SELECT * FROM Checks
                WHERE create_time >= ? AND result = 0
                '''

                cursor.execute(query, (time_for_db,))
                query_result = cursor.fetchone()

        except Exception as ex:
            logging.warning(f"{str(ex)}")

    if query_result:
        time_of_check = query_result[3]
        time_of_check_str = f"{time_of_check[:-7]}\n"

        check_result_str = ''

        # строка такого формата на входе https://инфарктанет.рф/ -> list index out of range;
        # https://finfarktanet.ru/ -> Cannot connect to host finfarktanet.ru:443 ssl:False [getaddrinfo failed];
        # https://tnimc.ru/ -> Элемент не найден;
        prep_check_result = query_result[2].split(';')[:-1]
        prev_str = f'Проверка {time_of_check_str}: ❌\n'

        check_result_str += prev_str

        for index in range(len(prep_check_result)):
            check_result_str += f"{str(index + 1)}. {prep_check_result[index]}\n"

        text = f"Результат:\n{check_result_str}"

        await context.bot.send_message(chat_id=CHAT_ID, text=text, disable_web_page_preview=True)


def from_json(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as urls:
        data = json.load(urls)
    return data
