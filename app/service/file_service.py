import os
import uuid

import filetype

from app.exceptions.file_exception import FileNullNameException, FileExtensionException, FileSizeException, \
    FileSignatureException
from app.models.conference_file import ConferenceFileType
from app.utils.transliterate import safe_filename_with_cyrillic


class FileService:
    def __init__(self, upload_folder: str,
                 thesis_allowed_extensions: set,
                 thesis_max_size: int,
                 proceedings_allowed_extensions: set,
                 proceedings_max_size: int,
                 conference_file_allowed_extensions: set,
                 conference_file_max_size: int):
        self.upload_folder = upload_folder
        self.thesis_allowed_extensions = thesis_allowed_extensions
        self.thesis_max_size = thesis_max_size
        self.proceedings_allowed_extensions = proceedings_allowed_extensions
        self.proceedings_max_size = proceedings_max_size
        self.conference_file_allowed_extensions = conference_file_allowed_extensions
        self.conference_file_max_size = conference_file_max_size

    EXTENSION_TO_KIND = {
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

    def save_thesis_file(self, file, conf_id):
        self.__validate_thesis_file(file)

        secured_filename = safe_filename_with_cyrillic(file.filename)

        file_path = self.__save_file(file, secured_filename, "theses", conf_id)

        return file_path, secured_filename

    def save_conference_file(self, file, conf_id, file_type: ConferenceFileType):
        if file_type == ConferenceFileType.PROCEEDINGS:
            self.__validate_proceedings_file(file)
        else:
            self.__validate_conference_file(file)

        secured_filename = safe_filename_with_cyrillic(file.filename)
        sub_folder = "proceedings" if file_type == ConferenceFileType.PROCEEDINGS else "files"
        file_path = self.__save_file(file, secured_filename, sub_folder, conf_id)

        return file_path, secured_filename

    def delete_files(self, files):
        if not files:
            return

        base_folder = self.upload_folder

        for file in files:
            full_path = os.path.join(base_folder, file.file_path)
            try:
                os.remove(full_path)
            except FileNotFoundError:
                pass

        folder_path = os.path.dirname(os.path.join(base_folder, files[0].file_path))
        try:
            os.rmdir(folder_path)
        except OSError:
            pass

    def __save_file(self, file, filename, sub_folder, conf_id):
        ext = self.__get_ext(filename)
        new_filename = f"{uuid.uuid4()}.{ext}"

        upload_dir = self.__get_folder_path(conf_id, sub_folder)
        file_path = os.path.join(upload_dir, new_filename)

        file.save(file_path)

        return_path = os.path.join(str(conf_id), sub_folder, new_filename)
        return return_path

    def __get_folder_path(self, conf_id, sub_folder):
        base = self.upload_folder
        path = os.path.join(base, str(conf_id), sub_folder)
        os.makedirs(path, exist_ok=True)
        return path

    def __validate_thesis_file(self, file):
        self.__validate_file(file, self.thesis_allowed_extensions, self.thesis_max_size)

    def __validate_proceedings_file(self, file):
        self.__validate_file(file, self.proceedings_allowed_extensions, self.proceedings_max_size)

    def __validate_conference_file(self, file):
        self.__validate_file(file, self.conference_file_allowed_extensions, self.conference_file_max_size)

    def __validate_file(self, file, allowed_extensions, max_size):
        self.__validate_filename(file.filename, allowed_extensions)
        self.__validate_file_size(file, max_size)
        self.__validate_file_signature(file)

    def __validate_filename(self, filename, allowed_extensions):
        if filename == '':
            raise FileNullNameException()

        ext = self.__get_ext(filename)

        if ext not in allowed_extensions:
            raise FileExtensionException(ext)

    def __validate_file_size(self, file, max_size):
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > max_size:
            raise FileSizeException(max_size // 1024 // 1024)

    def __validate_file_signature(self, file):
        ext = self.__get_ext(file.filename)

        file_start = file.read(8192)
        file.seek(0)

        kind = filetype.guess(file_start)

        if kind is None:
            raise FileSignatureException("Не удалось определить тип файла")

        expected_kind = self.EXTENSION_TO_KIND.get(ext)

        if kind.extension != expected_kind:
            raise FileSignatureException(f"Файл имеет расширение .{ext}, но внутри имеет данные типа .{kind.extension}")

    def __get_ext(self, filename):
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''