from datetime import date

from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from app.dto.dto import ThesisDTO
from app.exceptions.conflict_exception import ThesisAfterDeadlineException
from app.exceptions.not_found_exception import ApplicationNotFoundException, ThesisNotFoundException
from app.models.thesis import Thesis, ThesisStatus
from app.repository.thesis_repository import ThesisRepository
from app.service.application_service import ApplicationService
from app.service.conference_service import ConferenceService
from app.service.file_service import FileService


class ThesisService:
    """Управление тезисами участников: загрузка, смена статуса, удаление."""

    def __init__(
        self,
        conference_service: ConferenceService,
        application_service: ApplicationService,
        file_service: FileService,
        thesis_repository: ThesisRepository
    ) -> None:
        self.__repo = thesis_repository
        self.__conference_service = conference_service
        self.__application_service = application_service
        self.__file_service = file_service

    def create_thesis(self, conf_id: int, file: FileStorage, dto: ThesisDTO, session: Session) -> Thesis:
        """Загружает тезис участника. Проверяет дедлайн и наличие подтверждённой заявки по email."""
        conference = self.__conference_service.get_conference_by_id(conf_id, session)

        if conference.submission_deadline < date.today():
            raise ThesisAfterDeadlineException(conference.submission_deadline)

        application = self.__application_service.get_confirmed_application_by_conf_email(
            conf_id, dto.email, session
        )
        if not application:
            raise ApplicationNotFoundException(dto.email)

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

    def get_all_theses(self, session: Session) -> list[Thesis]:
        """Возвращает все тезисы без фильтрации."""
        return self.__repo.get_all(session)

    def get_thesis_by_id(self, thesis_id: int, session: Session) -> Thesis:
        """Возвращает тезис по ID. Выбрасывает ThesisNotFoundException если не найден."""
        thesis = self.__repo.get_by_id(thesis_id, session)
        if not thesis:
            raise ThesisNotFoundException(thesis_id)
        return thesis

    def update_thesis_status(self, thesis_id: int, status: str, session: Session) -> Thesis:
        """Меняет статус тезиса по строковому значению ThesisStatus."""
        thesis = self.get_thesis_by_id(thesis_id, session)
        thesis.status = ThesisStatus(status)
        return self.__repo.save(thesis, session)

    def delete_all_conference_theses_files(self, conf_id: int, session: Session) -> None:
        """Удаляет файлы всех тезисов конференции с диска."""
        theses = self.__repo.get_by_conf_id(conf_id, session)
        self.__file_service.delete_files(theses)

    def get_accepted_theses_with_applications(
        self, conf_id: int, session: Session
    ) -> list[tuple[Thesis, ...]]:
        """Возвращает принятые тезисы вместе с данными заявок для построения расписания."""
        return self.__repo.get_accepted_theses_with_applications(conf_id, session)
