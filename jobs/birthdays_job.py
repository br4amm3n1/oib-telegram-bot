from datetime import datetime, timedelta

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, CallbackContext, filters


NAME, SURNAME, BIRTHDAY = range(3)

def save_user_data(user_id: int, name: str, surname: str, birthday: str) -> None:
    with open("jobs/data/birthdays.txt", "a") as file:
        file.write(f"{user_id},{name},{surname},{birthday}\n")


def load_user_data() -> list:
    try:
        with open("jobs/data/birthdays.txt", "r") as file:
            return [line.strip().split(",") for line in file.readlines()]
    except FileNotFoundError:
        return []


def remove_user_data(user_id: int) -> bool:
    users_data = load_user_data()

    if str(user_id) in [str(user[0]) for user in users_data]:
        updated_data = [user for user in users_data if user[0] != str(user_id)]
    else:
        return False

    with open("jobs/data/birthdays.txt", "w") as file:
        for user in updated_data:
            file.write(",".join(user) + "\n")

    return True


async def subscribe(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id

    users_data = load_user_data()

    if str(user_id) not in [str(user[0]) for user in users_data]:
        await update.message.reply_text("Введите ваше имя:", reply_markup=ReplyKeyboardRemove())
        return NAME
    else:
        await update.message.reply_text("Вы уже подписаны.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


async def unsubscribe(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    result = remove_user_data(user_id)

    if result:
        await update.message.reply_text("Вы успешно отписались от уведомлений.",
                                        reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Вы не подписаны.",
                                        reply_markup=ReplyKeyboardRemove())


async def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите вашу фамилию:")
    return SURNAME


async def get_surname(update: Update, context: CallbackContext) -> int:
    context.user_data['surname'] = update.message.text
    await update.message.reply_text("Введите вашу дату рождения в формате ДД.ММ.ГГГГ:")
    return BIRTHDAY


async def get_birthday(update: Update, context: CallbackContext) -> int:
    try:
        birthday = datetime.strptime(update.message.text, "%d.%m.%Y").date()
        context.user_data['birthday'] = birthday.strftime("%d.%m.%Y")

        save_user_data(
            update.message.from_user.id,
            context.user_data['name'],
            context.user_data['surname'],
            context.user_data['birthday']
        )

        await update.message.reply_text("Спасибо! Вы подписались на уведомления.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Попробуйте снова в формате ДД.ММ.ГГГГ.")
        return BIRTHDAY


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Подписка отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def compare_dates(user_context: dict) -> str:
    today = datetime.today()
    next_week = today + timedelta(days=7)
    # next_month = today + relativedelta(months=1)

    today_str = today.strftime("%d.%m")
    next_week_str = next_week.strftime("%d.%m")
    # next_month_str = next_month.strftime("%d.%m")

    periods = {
        "today_str": today_str,
        "next_week_str": next_week_str,
        # "next_month_str": next_month_str
    }

    birthday_date = datetime.strptime(user_context['birthday'], "%d.%m.%Y").date()
    birthday_str = birthday_date.strftime("%d.%m")

    for name, period in periods.items():
        if birthday_str == period:
            if name == "today_str":
                return f"Сегодня день рождения у {user_context['name']} {user_context['surname']}! 🎉"
            if name == "next_week_str":
                return (f"Через неделю ({birthday_date.strftime('%d.%m.%Y')}) день рождения у "
                        f"{user_context['name']} {user_context['surname']}! 🎉")
            # if name == "next_month_str":
            #     return (f"Через месяц ({birthday_date.strftime('%d.%m.%Y')}) день рождения у "
            #             f"{user_context['name']} {user_context['surname']}! 🎉")

    return ""


async def check_birthdays(context: CallbackContext) -> None:
    users_data = load_user_data()

    for user in users_data:
        user_context = {
            'user_id': user[0],
            'name': user[1],
            'surname': user[2],
            'birthday': user[3]
        }

        text = compare_dates(user_context)

        if len(text) > 0:
            for other_user in users_data:
                if other_user[0] != user_context.get('user_id'):
                    await context.bot.send_message(chat_id=other_user[0], text=text)

SUBSCRIBE_HANDLER = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Подписаться на рассылку дней рождений']), subscribe)],
        states={
            NAME: [MessageHandler(filters.TEXT, get_name)],
            SURNAME: [MessageHandler(filters.TEXT, get_surname)],
            BIRTHDAY: [MessageHandler(filters.TEXT, get_birthday)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

UNSUBSCRIBE_HANDLER = MessageHandler(filters.Text(['Отписаться']), unsubscribe)
