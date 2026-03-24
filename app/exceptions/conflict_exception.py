from app.exceptions.exceptions import AppException


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message)

class ApplicationAfterDeadlineException(ConflictException):
    def __init__(self, date):
        message = f"Дедлайн для подачи заявки на участие в этой конференции уже прошел: {date}"
        super().__init__(message)

class ApplicationAlreadyExists(ConflictException):
    def __init__(self, email):
        message = f"Заявка с таким email {email} уже существует"
        super().__init__(message)

class ThesisAfterDeadlineException(ConflictException):
    def __init__(self, date):
        messages = f"Дедлайн для подачи тезисов уже прошел {date}"
        super().__init__(messages)