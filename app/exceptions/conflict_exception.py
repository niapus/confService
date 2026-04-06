from app.exceptions import AppException


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class ApplicationAfterDeadlineException(ConflictException):
    def __init__(self, date):
        message = f"Дедлайн подачи заявки истек {date}"
        super().__init__(message)

class ApplicationAlreadyExists(ConflictException):
    def __init__(self, email):
        message = f"Заявка с таким email {email} уже существует"
        super().__init__(message)

class ThesisAfterDeadlineException(ConflictException):
    def __init__(self, date):
        messages = f"Дедлайн подачи тезисов истек {date}"
        super().__init__(messages)