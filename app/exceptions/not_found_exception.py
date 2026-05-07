from app.exceptions import AppException


class NotFoundException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class ConferenceNotFoundException(NotFoundException):
    def __init__(self, conf_id):
        message = f"Конференция с id {conf_id} не найдена"
        super().__init__(message)

class ApplicationNotFoundException(NotFoundException):
    def __init__(self, identifier):
        message = f"Заявка {identifier} не найдена"
        super().__init__(message)

class ThesisNotFoundException(NotFoundException):
    def __init__(self, thesis_id):
        message = f"Файл тезисов с id {thesis_id} не найден"
        super().__init__(message)

class FileNotFoundException(NotFoundException):
    def __init__(self, file_name):
        message = f"Файл {file_name} не найден"
        super().__init__(message)