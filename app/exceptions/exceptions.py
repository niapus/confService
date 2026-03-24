class AppException(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

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