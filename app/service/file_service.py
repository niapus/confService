import os
import uuid

import filetype
from werkzeug.datastructures import FileStorage

from app.exceptions.file_exception import FileNullNameException, FileExtensionException, FileSizeException, \
    FileSignatureException
from app.models.conference_file import ConferenceFileType
from app.utils.transliterate import safe_filename_with_cyrillic


class FileService:
    """Валидация и сохранение загружаемых файлов на диск."""

    EXTENSION_TO_KIND: dict[str, str] = {
        'pdf': 'pdf',
        'docx': 'docx',
        'doc': 'doc',
        'ppt': 'ppt',
        'pptx': 'pptx',
        'jpg': 'jpg',
        'jpeg': 'jpg',
        'png': 'png',
        'zip': 'zip'
    }

    def __init__(
        self,
        upload_folder: str,
        thesis_allowed_extensions: set[str],
        thesis_max_size: int,
        proceedings_allowed_extensions: set[str],
        proceedings_max_size: int,
        conference_file_allowed_extensions: set[str],
        conference_file_max_size: int
    ) -> None:
        """
        Args:
            thesis_max_size: Максимальный размер файла тезисов в байтах.
            proceedings_max_size: Максимальный размер сборника тезисов в байтах.
            conference_file_max_size: Максимальный размер файла конференции в байтах.
        """
        self.upload_folder = upload_folder
        self.thesis_allowed_extensions = thesis_allowed_extensions
        self.thesis_max_size = thesis_max_size
        self.proceedings_allowed_extensions = proceedings_allowed_extensions
        self.proceedings_max_size = proceedings_max_size
        self.conference_file_allowed_extensions = conference_file_allowed_extensions
        self.conference_file_max_size = conference_file_max_size

    def save_thesis_file(self, file: FileStorage, conf_id: int) -> tuple[str, str]:
        """Валидирует и сохраняет файл тезисов. Возвращает (file_path, original_filename)."""
        self.__validate_thesis_file(file)
        secured_filename = safe_filename_with_cyrillic(file.filename)
        file_path = self.__save_file(file, secured_filename, "theses", conf_id)
        return file_path, secured_filename

    def save_conference_file(
        self, file: FileStorage, conf_id: int, file_type: ConferenceFileType
    ) -> tuple[str, str]:
        """Валидирует и сохраняет файл конференции. Возвращает (file_path, original_filename)."""
        if file_type == ConferenceFileType.PROCEEDINGS:
            self.__validate_proceedings_file(file)
        else:
            self.__validate_conference_file(file)

        secured_filename = safe_filename_with_cyrillic(file.filename)
        sub_folder = "proceedings" if file_type == ConferenceFileType.PROCEEDINGS else "files"
        file_path = self.__save_file(file, secured_filename, sub_folder, conf_id)
        return file_path, secured_filename

    def delete_files(self, files: list) -> None:
        """Удаляет файлы с диска и папку конференции, если она стала пустой.

        Args:
            files: Список объектов с атрибутом ``file_path`` (Thesis или ConferenceFile).
        """
        if not files:
            return

        for file in files:
            full_path = os.path.join(self.upload_folder, file.file_path)
            try:
                os.remove(full_path)
            except FileNotFoundError:
                pass

        folder_path = os.path.dirname(os.path.join(self.upload_folder, files[0].file_path))
        try:
            os.rmdir(folder_path)
        except OSError:
            pass

    def __save_file(self, file: FileStorage, filename: str, sub_folder: str, conf_id: int) -> str:
        ext = self.__get_ext(filename)
        new_filename = f"{uuid.uuid4()}.{ext}"
        upload_dir = self.__get_folder_path(conf_id, sub_folder)
        file.save(os.path.join(upload_dir, new_filename))
        return os.path.join(str(conf_id), sub_folder, new_filename)

    def __get_folder_path(self, conf_id: int, sub_folder: str) -> str:
        path = os.path.join(self.upload_folder, str(conf_id), sub_folder)
        os.makedirs(path, exist_ok=True)
        return path

    def __validate_thesis_file(self, file: FileStorage) -> None:
        self.__validate_file(file, self.thesis_allowed_extensions, self.thesis_max_size)

    def __validate_proceedings_file(self, file: FileStorage) -> None:
        self.__validate_file(file, self.proceedings_allowed_extensions, self.proceedings_max_size)

    def __validate_conference_file(self, file: FileStorage) -> None:
        self.__validate_file(file, self.conference_file_allowed_extensions, self.conference_file_max_size)

    def __validate_file(self, file: FileStorage, allowed_extensions: set[str], max_size: int) -> None:
        self.__validate_filename(file.filename, allowed_extensions)
        self.__validate_file_size(file, max_size)
        self.__validate_file_signature(file)

    def __validate_filename(self, filename: str, allowed_extensions: set[str]) -> None:
        if filename == '':
            raise FileNullNameException()
        ext = self.__get_ext(filename)
        if ext not in allowed_extensions:
            raise FileExtensionException(ext)

    def __validate_file_size(self, file: FileStorage, max_size: int) -> None:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > max_size:
            raise FileSizeException(max_size // 1024 // 1024)

    def __validate_file_signature(self, file: FileStorage) -> None:
        ext = self.__get_ext(file.filename)
        file_start = file.read(8192)
        file.seek(0)

        kind = filetype.guess(file_start)
        if kind is None:
            raise FileSignatureException("Не удалось определить тип файла")

        expected_kind = self.EXTENSION_TO_KIND.get(ext)
        if kind.extension != expected_kind:
            raise FileSignatureException(
                f"Файл имеет расширение .{ext}, но внутри имеет данные типа .{kind.extension}"
            )

    def __get_ext(self, filename: str) -> str:
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
