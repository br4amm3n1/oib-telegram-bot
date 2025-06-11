import os
import imaplib
import email
from email import policy

from telegram.ext import CallbackContext
from dotenv import load_dotenv

load_dotenv()
CHAT_ID = os.getenv('CHAT_ID')
IMAP_SERVER = os.getenv('IMAP_SERVER')
LOGIN = os.getenv('LOGIN_MAIL')
PASSWORD = os.getenv('PASSWORD_MAIL')


async def check_email_job(context: CallbackContext) -> None:
    '''
    Проверяет электронный почтовый ящик по указанному адресу и отправляет в групповой чат
    непрочитанные сообщения из него.
    :param context: CallbackContext
    :return: None
    '''
    mail_catalogs = ['INBOX', 'INBOX/check_minzdrav']
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(LOGIN, PASSWORD)

    for catalog in mail_catalogs:
        mail.select(catalog)

        status, messages = mail.search(None, 'UNSEEN')
        message_ids = messages[0].split()

        for msg_id in message_ids:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1], policy=policy.default)

                    subject = msg['subject']
                    from_ = msg['from']
                    date = msg['date']
                    body = ""

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode()
                    else:
                        body = msg.get_payload(decode=True).decode()

                    message_text = f"НОВОЕ ПИСЬМО:\n\n\nОт: {from_}\nТема: {subject}\nДата: {date}\n\n{body}"
                    await context.bot.send_message(chat_id=CHAT_ID, text=message_text)

    mail.logout()