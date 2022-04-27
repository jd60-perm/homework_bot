class NoEnvExpression(Exception):
    """Исключение отсутствия обязательных переменных окружения."""

    pass


class ApiUnreachable(Exception):
    """Исключение недоступности API Практикума."""

    pass


class SendMessageError(Exception):
    """Исключение невозможности отправки сообщения через Telegram."""

    pass


class OtherApiProblems(Exception):
    """Исключение прочих ошибок API Практикума."""

    pass
