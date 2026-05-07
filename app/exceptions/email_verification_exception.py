from app.exceptions import AppException


class EmailVerificationException(AppException):
    def __init__(self, message):
        super().__init__(message, status_code=400)