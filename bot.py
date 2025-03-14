import functools
import os
import datetime

from telegram import Update, ReplyKeyboardMarkup, MenuButtonCommands, BotCommand
from telegram.ext import Application, CallbackContext, CommandHandler
from dotenv import load_dotenv

from jobs.email_job import check_email_job
from jobs.birthdays_job import SUBSCRIBE_HANDLER, UNSUBSCRIBE_HANDLER, check_birthdays
from jobs.parser_job import check_sites, send_notifications_for_sites_checking

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')


def private_chat(func):
    @functools.wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.message.chat.type == "private":
            return func(update, context, *args, **kwargs)
        else:
            return update.message.reply_text("Эта команда доступна только в личных сообщениях с ботом.")
    return wrapper


async def set_commands(app: Application) -> None:
    commands = [
        BotCommand("start", "Получить описание возможностей бота"),
        BotCommand("menu", "Взаимодействовать с подпиской на уведомления"),
    ]

    await app.bot.set_my_commands(commands)
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def post_init(application: Application) -> None:
    #Сервер Telegram находится в часовом поясе UTC+7, значит нужно вычитать 7 часов из необходимого времени уведомления
    time =  datetime.time(hour=5, minute=0, second=0)

    application.job_queue.run_repeating(check_email_job, interval=3600, first=0)
    application.job_queue.run_repeating(check_birthdays, interval=86400, first=0)
    application.job_queue.run_repeating(check_sites, interval=14400, first=0)
    # application.job_queue.run_repeating(send_notifications_for_sites_checking, interval=80, first=0)
    application.job_queue.run_daily(send_notifications_for_sites_checking, time)

    await set_commands(application)


@private_chat
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Привет, я бот отдела информационной безопасности Томского НИМЦ.\n\n"
                                    "Для подписки на уведомления о днях рождений своих коллег введите "
                                    "команду /menu или воспользуйтесь меню слева от поля ввода сообщения.\n"
                                    "Если нужно прервать заполнение данных, введите /cancel.")


@private_chat
async def menu(update: Update, context: CallbackContext) -> None:
    buttons = [
        ['Подписаться на рассылку дней рождений'],
        ['Отписаться']
    ]

    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    await update.message.reply_text('Выберите опцию:', reply_markup=reply_markup)


def main() -> None:
    app = (Application.builder()
           .token(BOT_TOKEN)
           .post_init(post_init)
           .build())

    ch_start = CommandHandler("start", start)
    ch_menu = CommandHandler("menu", menu)

    app.add_handlers([ch_start, ch_menu, SUBSCRIBE_HANDLER, UNSUBSCRIBE_HANDLER])

    app.run_polling()


if __name__ == '__main__':
    main()

