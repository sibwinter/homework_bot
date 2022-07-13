
from http import HTTPStatus
import os
import time
import logging
from logging.handlers import RotatingFileHandler
from urllib.error import HTTPError

import telegram
import requests
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('program.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s,%(funcName)s,\
                %(lineno)d, %(message)s, %(name)s'
)
handler.setFormatter(formatter)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 5
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
    except telegram.error.TelegramError:
        raise()
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
        raise()


def check_response(response):
    """Проверяем ответ от API.

    Проверяем что данные полученные в ответе API корректны:
        - словарь ответа не пустой
        - в словаре есть нужные ключи: "homeworks"
    В случае некорректности логируем ошибки.
    """
    if (
        isinstance(response, dict)
        and isinstance(response['homeworks'], list)
        and isinstance(response['current_date'], int)
    ):
        logger.info('Статус ответа API проверен, все ок')
        return response['homeworks']
    else:
        raise TypeError('Unable to parse response, invalid JSON.')


def parse_status(homework):
    """Парсим статус домашней работы.

    Находим в словаре домашней работы значения ключей "homework_name"
    и "status". Если все хорошо то возвращаем строку с ответом для бота
    """
    if (
        homework.get('homework_name') is None
        or homework.get('status') is None
    ):
        raise KeyError('Нет статуса работы')

    homework_name = homework['homework_name']
    homework_status = homework['status']
    if HOMEWORK_VERDICTS.get(homework_status) is None:
        raise KeyError('Словарь HOMEWORK_VERDICTS',
                       f'не содержит такого ключа {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    logger.info('Статус работы изменился, новый статус: {verdict}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем переменные в окружении."""
    env_tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    if not all(env_tokens):
        return False
    else:
        logger.info('переменные окружения в порядке')
        return True


def main():
    """Основная логика работы бота."""  
    try:
        check_tokens()
    except ValueError:
        logger.critical('Переменные окружения не настроены!',
                        'Аварийное завершение работы программы')
        raise SystemExit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previouse_status = ''

    while True:

        try:
            response = get_api_answer(current_timestamp)

            try:
                check_response(response)
            except TypeError as e:
                logger.error(f'{e}: Ошибка парсинга данных, неверный JSON.')

            if check_response(response):
                homework = check_response(response)[0]
                try:
                    current_status = parse_status(homework)
                except KeyError('Нет статуса работы') as e:
                    logger.error(f'Нет статуса работы, ошика словаря: {e}')

                if current_status != previouse_status:
                    try:
                        send_message(bot, current_status)
                        current_timestamp = response['current_date']
                        previouse_status = current_status
                    except telegram.error.TelegramError as e:
                        logger.error(f'Сообщение не отправлено, ошибка : {e}')
                else:
                    logger.info('Статус не изменился')

            else:
                send_message(bot, 'статус домашней работы не изменился!')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
