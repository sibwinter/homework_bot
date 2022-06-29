# homework_api/api_praktikum.py
import requests
from pprint import pprint
url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
PRACTICUM_TOKEN = 'AQAAAAAPbkzJAAYckR9Mt0AI-EfAks6ieORiRQQ'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
payload = {'from_date': '0'}
# Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами params
homework_statuses = requests.get(url, headers=HEADERS, params=payload)
# Печатаем ответ API в формате JSON
pprint(homework_statuses.json()['homeworks'])
# А можно ответ в формате JSON привести к типам данных Python и напечатать и его
# print(homework_statuses.json())