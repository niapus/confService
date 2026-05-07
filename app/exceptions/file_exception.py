from app.exceptions import AppException


class FileException(AppException):
    def __init__(self, message):
        super().__init__(message, status_code=400)

class FileNullNameException(FileException):
    def __init__(self):
        super().__init__("Имя файла пустое")

class FileExtensionException(FileException):
    def __init__(self, current):
        message = f"Недопустимый тип файла {current}"
        super().__init__(message)

class FileSizeException(FileException):
    def __init__(self, size):
        message = f"Файл слишком большой. Максимальный размер {size}MB"
        super().__init__(message)

class FileSignatureException(FileException):
    def __init__(self, message):
        super().__init__(message)