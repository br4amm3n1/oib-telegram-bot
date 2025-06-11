import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import os

from telegram.ext import CallbackContext


load_dotenv()
CHAT_ID = os.getenv('CHAT_ID')

def compare_dates(date: str) -> str:
    today = datetime.today()
    in_2_week = today + timedelta(days=14)
    next_month = today + relativedelta(months=1)

    in_2_week_str = in_2_week.strftime("%d.%m")
    next_month_str = next_month.strftime("%d.%m")

    periods = {
        "in_2_week_str": in_2_week_str,
        "next_month_str": next_month_str
    }

    expiry_date = datetime.strptime(date, "%d.%m.%Y").date()
    expiry_date_str = expiry_date.strftime("%d.%m")

    for name, period in periods.items():
        if expiry_date_str == period:
            if name == "in_2_week_str":
                return f"Истекает через 2 недели"
            if name == "next_month_str":
                return f"Истекает через месяц"

    return ""

async def check_expiry_date_of_ds(context: CallbackContext) -> None:
    ds_csv = pd.read_csv('jobs/data/ds_info.csv', encoding='utf-8', sep=';')
    ds_csv_clean = ds_csv.dropna(subset=['Окончание действия сертификата']).copy()

    def format_row(row):
        expiry_date = row['Окончание действия сертификата']
        result = compare_dates(expiry_date)

        if result:
            return (
                f"| {row['ФИО'][:40]:<40} | "
                f"{row['Подразделение'][:18]:<18} | "
                f"{expiry_date[:10]:<15} | "
                f"{result:<15} |"
            )

    header = "| ФИО                                  | Подразделение      | Срок окончания | Статус          |\n"
    separator = "|--------------------------------------|--------------------|-----------------|-----------------|\n"

    table_rows = ds_csv_clean.apply(format_row, axis=1).str.cat(sep="\n")
    text_message = f"```\n{header}{separator}{table_rows}\n```"

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=text_message,
        parse_mode='MarkdownV2'
    )
