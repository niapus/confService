from pyexpat.errors import messages


class AppException(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class ConferenceNotFoundException(AppException):
    def __init__(self, conf_id):
        message = f"Конференция с id {conf_id} не найдена"
        super().__init__(message, status_code=404)

class ApplicationAfterDeadlineException(AppException):
    def __init__(self, date):
        message = f"Дедлайн для подачи заявки на участие в этой конференции уже прошел: {date}"
        super().__init__(message, status_code=409)

class ApplicationAlreadyExists(AppException):
    def __init__(self, email):
        message = f"Заявка с таким email {email} уже существует"
        super().__init__(message, status_code=409)

class ValidationException(AppException):
    def __init__(self, message):
        super().__init__(message, status_code=400)

class ApplicationNotFoundException(AppException):
    def __init__(self, email):
        message = f"Заявка с email {email} не найдена"
        super().__init__(message, status_code=404)

class ThesisNotFoundException(AppException):
    def __init__(self, id):
        message = f"Файл тезисов с id {id} не найден"
        super().__init__(message, status_code=404)

class FileNullNameException(AppException):
    def __init__(self):
        super().__init__("Имя файла пустое", status_code=400) #TODO

class FileExtensionException(AppException):
    def __init__(self, current, must):
        message = f"Недопустимый тип файла. Должен быть {must}, получен {current}"
        super().__init__(message, status_code=400) #TODO

class FileSizeException(AppException):
    def __init__(self, size):
        message = f"Файл слишком большой. Максимальный размер {size}MB"
        super().__init__(message, status_code=400) #TODO

class ThesisAfterDeadlineException(AppException):
    def __init__(self, date):
        messages = f"Дедлайн для подачи тезисов уже прошел {date}"
        super().__init__(messages, status_code=409)