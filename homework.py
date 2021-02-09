import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
print(TELEGRAM_TOKEN)


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
        if homework['status'] == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        elif homework['status'] == 'approved':
            verdict = ('Ревьюеру всё понравилось, '
                       'можно приступать к следующему уроку.')
        else:
            raise ValueError('Ответ сервера содержит неверный статус')

        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

    except (KeyError, ValueError) as e:
        logging.error(msg=f'Ошибка: {e}')
        return f'Ошибка: {e}'


def get_homework_statuses(current_timestamp):
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(
            API_URL, params=params, headers=headers
        )

        return homework_statuses.json()

    except requests.RequestException as error:
        raise error


def send_message(message, bot_client):
    logging.info('Отправлено сообщение в чат Telegram')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Запуск Telegram-бота')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(300)

        except Exception as e:
            logging.exception(msg=f'Ошибка: {e}')
            send_message(e, bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
