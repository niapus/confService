class AppException(Exception):
    """Базовое исключение приложения. Несёт HTTP-статус и сообщение для клиента."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code