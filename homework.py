
from http import HTTPStatus
import os
import time
import logging
from logging.handlers import RotatingFileHandler

import telegram
import requests
from dotenv import load_dotenv

import exceptions as exc


load_dotenv()


def logging_init():
    """Инициализируем конфиг логгера."""

    logging.basicConfig(
        filename='homework_bot/program.log',
        format='%(asctime)s, %(levelname)s,%(funcName)s,\
                %(lineno)d, %(message)s, %(name)s'
    )


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('bot.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в чат.

    Отправляем заранее сформированное сообщение через чат-бот.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except exc.SendMessageException as e:
        logger.error(f'Сообщение не отправлено, ошибка : {e}')
    else:
        logger.info(f'Сообщение отправлено: {message}')


def get_api_answer(current_timestamp):
    """Посылаем запрос к API и получаем ответ.

    Делаем запрос к API и проверяем все ли в порядке.
    Если статут ответа 200, то отпраляем в качестве
    значения функции словарь из json
    """
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise Exception('Ошибка при получении ответа с сервера')
        logger.info('Соединение с сервером устанолено')
        return response.json()
    except Exception as e:
        raise Exception(e)


def check_response(response):
    """Проверяем ответ от API.

    Проверяем что данные полученные в ответе API корректны:
        - словарь ответа не пустой
        - в словаре есть нужные ключи: "homeworks"
    В случае некорректности логируем ошибки.
    """
    try:
        if (
                isinstance(response, dict)
                and isinstance(response['homeworks'], list)
        ):
            return response['homeworks']
    except TypeError as e:
        logger.error(f'{e}: Unable to parse response, invalid JSON.')
    else:
        logger.error('Нет нужных ключей в ответе API')
        logger.info('Статус ответа API проверен, все ок')
        raise ()


def parse_status(homework):
    """Парсим статус домашней работы.

    Находим в словаре домашней работы значения ключей "homework_name"
    и "status". Если все хорошо то возвращаем строку с ответом для бота
    """

    if homework['homework_name'] is None or homework['status'] is None:
        raise KeyError('Нет статуса работы')

    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_VERDICTS[homework_status]
    logger.info('Статус работы изменился, новый статус: {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем переменные в окружении."""
    if (PRACTICUM_TOKEN is None
       or TELEGRAM_TOKEN is None
       or TELEGRAM_CHAT_ID is None):
        logger.critical('отсутствуют обязательные переменные окружения')
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previouse_status = ''

    while True:

        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            current_status = parse_status(homework)
            if current_status != previouse_status:
                send_message(bot, current_status)
            else:
                logger.debug('Статус не изменился')

            time.sleep(RETRY_TIME)
            current_timestamp = int(time.time())
            previouse_status = current_status

        except exc.MainFunctionException as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            send_message(bot, 'статус домашней работы не изменился!')


if __name__ == '__main__':
    logging_init()
    main()
