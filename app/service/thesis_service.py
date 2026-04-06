import os

from app.exceptions.conflict_exception import ThesisAfterDeadlineException
from app.exceptions.file_exception import FileNullNameException, FileExtensionException, FileSizeException
from app.exceptions.not_found_exception import ApplicationNotFoundException, ThesisNotFoundException
from app.repository.thesis_repository import ThesisRepository
from app.service import ConferenceService, ApplicationService
from app.models.thesis import Thesis, ThesisStatus
from datetime import date
from flask import current_app

from app.service.file_service import FileService


class ThesisService:
    def __init__(self, conference_service: ConferenceService, application_service: ApplicationService,
                 file_service: FileService):
        self.__repo = ThesisRepository()
        self.__conference_service = conference_service
        self.__application_service = application_service
        self.__file_service = file_service

    def create_thesis(self, conf_id, file, dto, session):
        conference = self.__conference_service.get_conference_by_id(conf_id, session)

        if conference.submission_deadline < date.today():
            raise ThesisAfterDeadlineException(conference.submission_deadline)

        application = self.__application_service.get_application_by_conf_email(conf_id, dto.email, session)
        if not application:
            raise ApplicationNotFoundException(dto.email)

        self.__validate_file(file)

        file_path, secured_filename = self.__file_service.save_thesis_file(file, conf_id)

        thesis = Thesis(
            application_id=application.id,
            authors=dto.authors,
            title=dto.title,
            file_path=file_path,
            file_name=secured_filename,
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
        self.__file_service.delete_thesis_files(theses)

    def __validate_file(self, file):
        self.__validate_filename(file.filename)
        self.__validate_file_size(file)

    def __validate_filename(self, filename):
        if filename == '':
            raise FileNullNameException()

        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if ext != "pdf":
            raise FileExtensionException(ext, "pdf")

    def __validate_file_size(self, file):
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > current_app.config.get("MAX_CONTENT_LENGTH"):
            raise FileSizeException(current_app.config.get("MAX_CONTENT_LENGTH") // 1024 // 1024)