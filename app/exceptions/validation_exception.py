from app.exceptions import AppException


class ValidationException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)