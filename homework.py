import json
import time
from dotenv import load_dotenv
import requests
import telegram

load_dotenv()


PRACTICUM_TOKEN = 'AQAAAAAPbkzJAAYckR9Mt0AI-EfAks6ieORiRQQ'
TELEGRAM_TOKEN = '5579843922:AAHb9Q1IAAZIUtHHYdlepHh1fuPmqhpmgOA'
TELEGRAM_CHAT_ID = 526909696

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    ...


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            raise requests.exceptions.RequestException 
        return response.json()
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)




def check_response(response):
    if response == {}:
        raise TypeError('Пустой словарь в ответе')


    if (isinstance(response, dict) and 
        isinstance(response['homeworks'], list)):
        return response['homeworks']
    else:
        raise TypeError('Unable to parse response, invalid JSON.')




def parse_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']


    verdict = HOMEWORK_STATUSES[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if (PRACTICUM_TOKEN == None or 
        TELEGRAM_TOKEN == None or 
        TELEGRAM_CHAT_ID == None or 
        PRACTICUM_TOKEN == '' or 
        TELEGRAM_TOKEN == '' or 
        TELEGRAM_CHAT_ID == ''):
        return False
    else:
        return True



def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    ...

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            parse_status(homework)

            current_timestamp = ...
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
