from app.exceptions import AppException


class ValidationException(AppException):
    """Ошибка бизнес-валидации входных данных (HTTP 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)