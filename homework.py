from http import HTTPStatus
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from urllib.error import HTTPError

import telegram
import requests
from dotenv import load_dotenv

from exceptions import HomeworkBotException, TelegramException


load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'logs\\program.log',
    maxBytes=50000000,
    backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s,%(funcName)s,\
                %(lineno)d, %(message)s, %(name)s'
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
    except telegram.error.TelegramError as e:
        raise TelegramException(
            f'Сообщение не отправлено: {message}.',
            f'Ошибка telegram-bot: {e}')
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
            raise HTTPError('Ошибка при получении ответа с сервера.',
                            f'Код ответа: {response.status_code}')
        logger.info('Соединение с сервером устанолено')
        return response.json()
    except requests.exceptions.RequestException(
        'Не удалось получить ответ от сервера.'
    ):
        raise HomeworkBotException('Не удалось получить ответ от сервера.')


def check_response(response):
    """Проверяем ответ от API.

    Проверяем что данные полученные в ответе API корректны:
        - словарь ответа не пустой
        - в словаре есть нужные ключи: "homeworks"
    В случае некорректности логируем ошибки.
    """
    if isinstance(response, dict) is False:
        raise TypeError(
            'ответ сервера не является словарем JSON.')
    if response.get('homeworks') is None:
        raise KeyError(
            'Нет ключа "homeworks" в словаре response')
    if response.get('current_date') is None:
        raise KeyError(
            'Нет ключа "current_date" в словаре response')
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Значение словаря "homeworks" не является списком.')
    if not isinstance(response['current_date'], int):
        raise KeyError(
            'Значение словаря "current_date" не является целым числом.')
    return response['homeworks']


def parse_status(homework):
    """Парсим статус домашней работы.

    Находим в словаре домашней работы значения ключей "homework_name"
    и "status". Если все хорошо то возвращаем строку с ответом для бота
    """
    if not homework.get('homework_name', None):
        raise KeyError(
            'Нет ключа "homework_name" в словаре homework')
    if not homework.get('status', None):
        raise KeyError(
            'Нет ключа "status" в словаре homework')

    homework_name = homework['homework_name']
    homework_status = homework['status']
    if HOMEWORK_VERDICTS.get(homework_status) is None:
        raise HomeworkBotException(
            'Словарь HOMEWORK_VERDICTS',
            f'не содержит такого ключа {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    logger.info('Статус работы изменился, новый статус: {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем переменные в окружении."""
    env_tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return all(env_tokens)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical("Отсутствуют переменные окружения")
        raise SystemExit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previouse_status = ''

    while True:

        try:
            response = get_api_answer(current_timestamp)
            if (
                check_response(response)
                and not check_response(response) is None
            ):
                homework = check_response(response)[0]
                current_status = parse_status(homework)
                if current_status != previouse_status:
                    try:
                        send_message(bot, current_status)
                        current_timestamp = response['current_date']
                        previouse_status = current_status
                    except TelegramException as e:
                        logger.error(f'Сообщение не отправлено, ошибка : {e}')
                else:
                    logger.info('Статус не изменился')

            else:
                send_message(bot, 'Статус домашней работы не изменился!')

        except HomeworkBotException as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы: {error}')
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
