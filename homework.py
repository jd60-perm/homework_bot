import telegram
import requests
import sys
import os
import logging
import time
from dotenv import load_dotenv
import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

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
    except Exception as error:
        raise exceptions.SendMessageError(
            f'Ошибка при отправке сообщения в Telegram: {error}'
        )
    else:
        logger.info('Удачная отправка сообщения в Telegram')
        pass


def get_api_answer(current_timestamp):
    """Получение ответа от API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == 404:
        raise exceptions.ApiUnreachable(
            'Недоступность эндпоинта Практикума. Ошибка 404'
        )
    elif response.status_code != 200:
        raise exceptions.OtherApiProblems('Проблема API')
    else:
        return(response.json())


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
    if (homework_status in HOMEWORK_STATUSES):
        verdict = HOMEWORK_STATUSES.get(homework_status)
    else:
        raise KeyError(
            'Недокументированный статус домашней работы, '
            'обнаруженный в ответе API'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия необходимых токенов и ID чата в окружении."""
    return (PRACTICUM_TOKEN is not None) and \
           (TELEGRAM_TOKEN is not None) and \
           (TELEGRAM_CHAT_ID is not None)


def stop_without_tokens():
    """Без вынесения этого в отдельную функцию.
    PEP8 ругается, что main() function is too complex.
    """
    try:
        if not check_tokens():
            raise exceptions.NoEnvExpression(
                'Не хватает одной или нескольких переменных окружения.'
            )
    except exceptions.NoEnvExpression:
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
            logger.error('Сбой при отправке сообщения в Telegram')
            pass
        except exceptions.ApiUnreachable:
            log_last_message = 'Недоступность эндпоинта practicum.yandex'
            logger.error(log_last_message)
            pass
        except TypeError:
            log_last_message = 'Некорректный формат ответа API'
            logger.error(log_last_message)
            pass
        except KeyError:
            log_last_message = 'Отсутствие ожидаемых ключей в ответе API'
            logger.error(log_last_message)
            pass
        except exceptions.OtherApiProblems:
            log_last_message = 'Проблема при запросе к API'
            logger.error(log_last_message)
            pass
        except Exception as error:
            log_last_message = f'Сбой в работе программы: {error}'
            logger.error(log_last_message)
        finally:
            if log_last_message != log_prev_message:
                send_message(bot, log_last_message)
                log_prev_message = log_last_message
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
