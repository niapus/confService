from app.exceptions import AppException


class EmailVerificationException(AppException):
    """Ошибка верификации email через JWT-токен (HTTP 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)