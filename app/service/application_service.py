from app.exceptions.exceptions import ApplicationAfterDeadlineException, ApplicationAlreadyExists, ValidationException
from app.mapper.application_mapper import ApplicationMapper
from app.repository.application_repository import ApplicationRepository
from app.service import ConferenceService
from app.models.application import *
from datetime import date


class ApplicationService:
    def __init__(self, conference_service: ConferenceService):
        self.__repo = ApplicationRepository()
        self.__mapper = ApplicationMapper()
        self.__conf_service = conference_service

    def create_application(self, conf_id, app_dto, session):
        conference = self.__conf_service.get_conference_by_id(conf_id, session)

        if conference.registration_deadline < date.today():
            raise ApplicationAfterDeadlineException(conference.registration_deadline)

        if app_dto.birth_date > date.today():
            raise ValidationException("День рождения не может быть в будущем")

        existing = self.get_application_by_conf_email(conf_id, app_dto.email, session) #TODO
        if existing:
            raise ApplicationAlreadyExists(app_dto.email)

        application = Application()

        self.__fill_application(application, app_dto)
        application.conference_id = conf_id

        self.__repo.save(application, session)
        return application

    def get_application_by_conf_email(self, conf_id, email, session):
        application = self.__repo.find_application_by_conf_email(conf_id, email, session)
        return application

    def get_full_applications_for_conference(self, conf_id, session):
        self.__conf_service.exists(conf_id, session)

        applications = self.__repo.get_full_applications_for_conference(conf_id, session)

        data = self.__mapper.applications_to_full_applications_dto(applications)

        return data

    def __fill_application(self, application, dto):
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