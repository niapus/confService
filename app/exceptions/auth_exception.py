from app.exceptions import AppException


class AuthException(AppException):
    def __init__(self, message):
        super().__init__(message, status_code=401)

class ForbiddenException(AuthException):
    def __init__(self):
        super().__init__("Доступ запрещен")
        self.status_code=403

class InvalidCredentialsException(AuthException):
    def __init__(self):
        super().__init__("Неверный логин или пароль")