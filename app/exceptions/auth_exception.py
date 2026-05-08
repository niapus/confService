from app.exceptions import AppException


class AuthException(AppException):
    """Ошибка аутентификации (HTTP 401)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=401)


class ForbiddenException(AuthException):
    """Доступ к ресурсу запрещён (HTTP 403)."""

    def __init__(self) -> None:
        super().__init__("Доступ запрещен")
        self.status_code = 403


class InvalidCredentialsException(AuthException):
    """Неверный логин или пароль."""

    def __init__(self) -> None:
        super().__init__("Неверный логин или пароль")