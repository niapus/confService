import os
from werkzeug.utils import secure_filename
from app.repository.thesis_repository import ThesisRepository
from app.service import ConferenceService, ApplicationService
from app.models.thesis import Thesis, ThesisStatus
import uuid
from flask import current_app


class ThesisService:
    def __init__(self, conference_service: ConferenceService, application_service: ApplicationService):
        self.__repo = ThesisRepository()
        self.__conference_service = conference_service
        self.__application_service = application_service

    def create_thesis(self, conf_id, file, data, session):
        conference = self.__conference_service.get_conference_by_id(conf_id, session)

        application = self.__application_service.get_application_by_conf_email(conf_id, data.get("email"), session)
        filename = file.filename
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        original_filename = secure_filename(filename)
        new_filename = f"{uuid.uuid4()}.{ext}"

        upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER"), str(conf_id))
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, new_filename)

        file.save(file_path)

        thesis = Thesis(
            conference_id=conf_id,
            surname=data.get("surname"),
            name=data.get("name"),
            patronymic=data.get("patronymic"),
            email=data.get("email"),
            title=data.get("title"),
            file_path=file_path,
            file_name=original_filename,
            status=ThesisStatus.PENDING
        )

        return self.__repo.save(thesis, session)

    def get_all_theses(self, session):
        return self.__repo.get_all(session)

    def update_thesis_status(self, thesis_id, status, session):
        thesis = self.__repo.get_by_id(thesis_id, session)
        new_status = ThesisStatus(status)
        thesis.status = new_status
        self.__repo.save(thesis, session)

    def delete_conference_theses_files(self, conf_id, session):
        theses = self.__repo.get_by_conf_id(conf_id, session)
        for thesis in theses:
            file_path = thesis.file_path
            if os.path.exists(file_path):
                os.remove(file_path)

        folder_path = os.path.dirname(theses[0].file_path)
        if os.path.exists(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)