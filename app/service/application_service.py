from app.exceptions.exceptions import ApplicationAfterDeadlineException, ApplicationAlreadyExists, ValidationException
from app.mapper.application_mapper import ApplicationMapper
from app.repository.application_repository import ApplicationRepository
from app.service import ConferenceService
from app.models.application import *
from datetime import datetime, date


class ApplicationService:
    def __init__(self, conference_service: ConferenceService):
        self.__repo = ApplicationRepository()
        self.__mapper = ApplicationMapper()
        self.__conf_service = conference_service

    def create_application(self, conf_id, application_data, session):
        conference = self.__conf_service.get_conference_by_id(conf_id, session)

        if conference.registration_deadline < date.today():
            raise ApplicationAfterDeadlineException(conference.registration_deadline)

        validated_data = self.__validate_data(application_data)
        existing = self.get_application_by_conf_email(conf_id, validated_data.get('email'), session)

        if existing:
            raise ApplicationAlreadyExists(validated_data.get('email'))

        application = Application()

        converted_data = self.__convert_application_data(validated_data)

        for field, value in converted_data.items():
            if hasattr(application, field):
                setattr(application, field, value)

        application.conference_id = conf_id
        self.__repo.save(application, session)
        return application

    def get_application_by_conf_email(self, conf_id, email, session):
        application = self.__repo.find_application_by_conf_email(conf_id, email, session)
        return application

    def get_full_applications(self, conf_id, session):
        conference = self.__conf_service.exists(conf_id, session)

        query_result = self.__repo.get_full_applications(conf_id, session)

        data = self.__mapper.from_query_result_to_full_application_dto(query_result)

        return data

    def __convert_application_data(self, data):
        result = data
        statuses = data.get('status', [])
        result.update({
            "is_worker": "worker" in statuses,
            "is_student": "student" in statuses,
            "birth_date": datetime.strptime(data['birth_date'], '%Y-%m-%d').date(),
            "gender": GenderEnum(data['gender']),
            "degree": DegreeEnum(data['degree']),
            "participation_format": ParticipationFormatEnum(data["participation_format"]),
            "study_level": EducationEnum(data['study_level']) if "study_level" in data and data["study_level"] else None
        })

        return result

    def __validate_data(self, data):
        cleaned = self.__clean_data(data)

        required_values = ['surname', 'name', 'email']
        if data.get("is_worker"):
            required_values = required_values + ['work_name', 'work_place', 'work_position']
        if data.get("is_student"):
            required_values = required_values + ['study_name', 'study_place', 'study_level']

        for key in required_values:
            value = cleaned.get(key)
            if not value:
                raise ValidationException(f"Обязательное поле {key} не может быть пустым")

        birth_date = datetime.strptime(cleaned['birth_date'], '%Y-%m-%d').date()
        if birth_date > date.today():
            raise ValidationException(f"Дата рождения не может быть в будущем")

        return cleaned

    def __clean_data(self, data):
        cleaned = {}

        for key, value in data.items():
            if isinstance(value, str): #Кроме флагов
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value

        return cleaned