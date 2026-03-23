import os
from werkzeug.utils import secure_filename

from app.exceptions.exceptions import ApplicationNotFoundException, ThesisNotFoundException, ValidationException, \
    FileNullNameException, FileExtensionException, FileSizeException, ThesisAfterDeadlineException
from app.repository.thesis_repository import ThesisRepository
from app.service import ConferenceService, ApplicationService
from app.models.thesis import Thesis, ThesisStatus
import uuid
from datetime import date
from flask import current_app


class ThesisService:
    def __init__(self, conference_service: ConferenceService, application_service: ApplicationService):
        self.__repo = ThesisRepository()
        self.__conference_service = conference_service
        self.__application_service = application_service

    def create_thesis(self, conf_id, file, data, session):
        conference = self.__conference_service.get_conference_by_id(conf_id, session)

        if conference.submission_deadline < date.today():
            raise ThesisAfterDeadlineException(conference.submission_deadline)

        application = self.__application_service.get_application_by_conf_email(conf_id, data.get("email"), session)
        if not application:
            raise ApplicationNotFoundException(data.get("email"))

        #TODO проверка уже отправленных тезисов с таким названием
        valid_data = self.__validate_data(data)

        original_filename, ext = self.__validate_file(file)
        new_filename = f"{uuid.uuid4()}.{ext}"

        upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER"), str(conf_id))
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, new_filename)

        file.save(file_path)

        thesis = Thesis(
            application_id=application.id,
            authors=valid_data.get("authors"),
            title=valid_data.get("title"),
            file_path=file_path,
            file_name=original_filename,
            status=ThesisStatus.PENDING
        )

        return self.__repo.save(thesis, session)

    def get_all_theses(self, session):
        return self.__repo.get_all(session)

    def get_thesis_by_id(self, thesis_id, session):
        thesis = self.__repo.get_by_id(thesis_id, session)

        if not thesis:
            raise ThesisNotFoundException(thesis_id)
        return thesis

    def update_thesis_status(self, thesis_id, status, session):
        thesis = self.get_thesis_by_id(thesis_id, session)
        new_status = ThesisStatus(status)
        thesis.status = new_status
        self.__repo.save(thesis, session)

    def delete_conference_theses_files(self, conf_id, session):
        theses = self.__repo.get_by_conf_id(conf_id, session)

        if len(theses) == 0:
            return

        for thesis in theses:
            file_path = thesis.file_path
            if os.path.exists(file_path):
                os.remove(file_path)

        folder_path = os.path.dirname(theses[0].file_path)
        if os.path.exists(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)

    def __validate_data(self, data):
        cleaned = self.__clean_data(data)

        str_values = ['authors', 'title']

        for key in str_values:
            if not cleaned.get(key):
                raise ValidationException(f"Обязательное поле {key} не может быть пустым")

        return cleaned

    def __clean_data(self, data):
        cleaned = {}

        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value

        return cleaned

    def __validate_file(self, file):
        if file.filename == '':
            raise FileNullNameException()

        filename = secure_filename(file.filename) #TODO
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if ext != "pdf":
            raise FileExtensionException(ext, "pdf")

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > current_app.config.get("MAX_CONTENT_LENGTH"):
            raise FileSizeException(current_app.config.get("MAX_CONTENT_LENGTH") // 1024 // 1024)

        return (filename, ext)