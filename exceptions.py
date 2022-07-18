
class NotSendingMessageException(Exception):
    """Класс исключений для ошибок отправки сообщений телеграм-бота."""

    """Логирует ошибки, но не отправляет их в телеграм."""

    pass


class RequestAPIException(Exception):
    """Класс исключений для проверки ответа API."""

    """Логируются ошибки и отпраляются в телеграм."""

    pass
