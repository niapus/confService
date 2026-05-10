from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dto.dto import ApplicationDTO, FullApplicationDTO
from app.exceptions.conflict_exception import ApplicationAfterDeadlineException, ApplicationAlreadyExists
from app.exceptions.not_found_exception import ApplicationNotFoundException
from app.exceptions.validation_exception import ValidationException
from app.mapper.application_mapper import ApplicationMapper
from app.models.application import Application, ApplicationStatus
from app.repository.application_repository import ApplicationRepository
from app.service.conference_service import ConferenceService


class ApplicationService:
    """Управление заявками участников конференций."""

    def __init__(
        self,
        conference_service: ConferenceService,
        application_repository: ApplicationRepository,
        application_mapper: ApplicationMapper,
        verification_enabled: bool
    ) -> None:
        self.__repo = application_repository
        self.__mapper = application_mapper
        self.__conf_service = conference_service
        self.__verification_enabled = verification_enabled

    def create_application(self, conf_id: int, app_dto: ApplicationDTO, session: Session) -> Application:
        """Создаёт заявку участника. Проверяет дедлайн, дату рождения и дубликаты по email."""
        conference = self.__conf_service.get_conference_by_id(conf_id, session)

        if conference.registration_deadline < date.today():
            raise ApplicationAfterDeadlineException(conference.registration_deadline)

        if app_dto.birth_date > date.today():
            raise ValidationException("День рождения не может быть в будущем")

        existing = self.get_confirmed_application_by_conf_email(conf_id, app_dto.email, session)
        if existing:
            raise ApplicationAlreadyExists(app_dto.email)

        self.__repo.delete_unconfirmed_by_conf_email(conf_id, app_dto.email, session)

        application = Application()
        self.__fill_application(application, app_dto, conf_id)
        try:
            self.__repo.save(application, session)
        except IntegrityError:
            raise ApplicationAlreadyExists(app_dto.email)
        return application

    def get_confirmed_application_by_conf_email(
        self, conf_id: int, email: str, session: Session
    ) -> Application | None:
        """Возвращает подтверждённую заявку по конференции и email, или None если не найдена."""
        return self.__repo.find_confirmed_application_by_conf_email(conf_id, email, session)

    def get_full_applications_for_conference(self, conf_id: int, session: Session) -> list[FullApplicationDTO]:
        """Возвращает список FullApplicationDTO для всех заявок конференции."""
        applications = self.__repo.get_full_applications_for_conference(conf_id, session)
        return self.__mapper.applications_to_full_applications_dto(applications)

    def get_application_from_schedule(self, conf_id: int, session: Session) -> list[Application]:
        """Возвращает заявки, включённые в расписание конференции."""
        self.__conf_service.exists(conf_id, session)
        return self.__repo.get_applications_from_schedule(conf_id, session)

    def get_all_applications(self, session: Session) -> list[Application]:
        """Возвращает все заявки без фильтрации."""
        return self.__repo.get_all_confirmed(session)

    def get_by_id(self, app_id: int, session: Session) -> Application:
        """Возвращает заявку по ID. Выбрасывает ApplicationNotFoundException если не найдена."""
        application = self.__repo.get_by_id(app_id, session)
        if not application:
            raise ApplicationNotFoundException(app_id)
        return application

    def cleanup_unconfirmed_older_than(self, days: int, session: Session) -> int:
        """Удаляет неподтверждённые заявки старше указанного количества дней."""
        return self.__repo.delete_unconfirmed_older_than(days, session)

    def set_status(self, application: Application, status: ApplicationStatus, session: Session) -> None:
        """Устанавливает статус заявки и сохраняет изменение."""
        application.status = status
        self.__repo.save(application, session)

    def __fill_application(self, application: Application, dto: ApplicationDTO, conf_id: int) -> None:
        application.surname = dto.surname
        application.name = dto.name
        application.patronymic = dto.patronymic
        application.gender = dto.gender
        application.birth_date = dto.birth_date
        application.degree = dto.degree
        application.is_worker = dto.is_worker
        application.is_student = dto.is_student
        application.work_name = dto.work_name
        application.work_place = dto.work_place
        application.work_position = dto.work_position
        application.study_name = dto.study_name
        application.study_place = dto.study_place
        application.study_level = dto.study_level
        application.participation_format = dto.participation_format
        application.email = dto.email
        application.conference_id = conf_id
        application.status = (
            ApplicationStatus.UNCONFIRMED if self.__verification_enabled
            else ApplicationStatus.CONFIRMED
        )
