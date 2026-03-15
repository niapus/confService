from app.core.database import Session
from app.repository.application_repository import ApplicationRepository
from app.service import ConferenceService
from app.models.application import *
from datetime import datetime


class ApplicationService:
    def __init__(self, conference_service: ConferenceService):
        self.__repo = ApplicationRepository()
        self.__conf_service = conference_service

    def create_application(self, conf_id, application_data, session):
        conference = self.__conf_service.get_conference_by_id(conf_id, session)

        application = Application()

        converted_data = self.__convert_application_data(application_data)

        for field, value in converted_data.items():
            if hasattr(application, field):
                setattr(application, field, value)

        application.conference_id = conf_id
        self.__repo.save(application, session)
        return application

    def get_application_by_conf_email(self, conf_id, email, session):
        application = self.__repo.find_application_by_conf_email(conf_id, email, session)
        return application

    def __convert_application_data(self, data):
        result = dict(data)
        result.update({
            "is_worker": "worker" in data.getlist('status'),
            "is_student": "student" in data.getlist('status'),
            "gender": GenderEnum(data['gender']),
            "degree": DegreeEnum(data['degree']),
            "birth_date": datetime.strptime(data['birth_date'], '%Y-%m-%d').date(),
            "participation_format": ParticipationFormatEnum(data["participation_format"]),
            "study_level": EducationEnum(data['study_level']) if "study_level" in data and data["study_level"] else None
        })

        return result