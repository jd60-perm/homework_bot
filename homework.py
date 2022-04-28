import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions
import settings

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сформированного сообщение через бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        raise exceptions.SendMessageError(
            f'Ошибка при отправке сообщения в Telegram: {error}'
        )
    else:
        logger.info('Удачная отправка сообщения в Telegram')


def get_api_answer(current_timestamp):
    """Получение ответа от API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            settings.ENDPOINT, headers=HEADERS, params=params
        )
        if response.status_code == HTTPStatus.NOT_FOUND:
            raise exceptions.ApiUnreachable(
                'Недоступность эндпоинта Практикума. Ошибка 404'
            )
        elif response.status_code != HTTPStatus.OK:
            raise exceptions.OtherApiProblems('Проблема API')
        else:
            return response.json()
    except requests.exceptions.RequestException as error:
        log_last_message = f'Проблема при запросе к API {error}'
        logger.error(log_last_message)


def check_response(response):
    """Проверка корректности ответа от API и выделение нужной информации."""
    key = 'homeworks'
    if isinstance(response, dict):
        if key in response:
            homeworks = response.get(key)
            if isinstance(homeworks, list):
                return homeworks
            else:
                raise TypeError(
                    'Некорректный ответ API. Формат отличается от ожидаемого'
                )
        else:
            raise KeyError(
                'Отсутствие ожидаемых ключей в ответе API'
            )
    else:
        raise TypeError(
            'Некорректный ответ API. Формат отличается от ожидаемого'
        )


def parse_status(homework):
    """Формирование сообщения для отправки от бота.
    из выделенной информации от API.
    """
    if ('homework_name' in homework) and ('status' in homework):
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
    else:
        raise KeyError(
            'Отсутствие ожидаемых ключей в ответе API'
        )
    if (homework_status in settings.HOMEWORK_STATUSES):
        verdict = settings.HOMEWORK_STATUSES.get(homework_status)
    else:
        raise KeyError(
            'Недокументированный статус домашней работы, '
            'обнаруженный в ответе API'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия необходимых токенов и ID чата в окружении."""
    return all((
        PRACTICUM_TOKEN is not None,
        TELEGRAM_TOKEN is not None,
        TELEGRAM_CHAT_ID is not None
    ))


def stop_without_tokens():
    """Без вынесения этого в отдельную функцию.
    PEP8 ругается, что main() function is too complex.
    """
    if not check_tokens():
        logger.critical(
            'Отсутствие обязательных переменных окружения при запуске бота'
        )
        sys.exit()


def main():
    """Основная логика работы бота."""
    stop_without_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    log_last_message = ''
    log_prev_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                status = parse_status(homeworks[0])
                send_message(bot, status)
            else:
                logger.debug('Отсутствие в ответе новых статусов')
        except exceptions.SendMessageError:
            log_last_message = 'Сбой при отправке сообщения в Telegram'
        except TypeError:
            log_last_message = 'Некорректный формат ответа API'
        except KeyError:
            log_last_message = 'Отсутствие ожидаемых ключей в ответе API'
        except exceptions.ApiUnreachable:
            log_last_message = 'Недоступность эндпоинта practicum.yandex'
        except exceptions.OtherApiProblems:
            log_last_message = 'Проблема при запросе к API'
        except Exception as error:
            log_last_message = f'Сбой в работе программы: {error}'
        finally:
            logger.error(log_last_message)
            if log_last_message != log_prev_message:
                send_message(bot, log_last_message)
                log_prev_message = log_last_message
            current_timestamp = int(time.time())
            time.sleep(settings.RETRY_TIME)


if __name__ == '__main__':
    main()
