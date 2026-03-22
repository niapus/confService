from app.exceptions.exceptions import ConferenceNotFoundException, ValidationException
from app.repository.conference_repository import ConferenceRepository
from datetime import date, datetime
from app.models.conference import Conference
from app.service.markdown_service import MarkdownService

class ConferenceService:

    def __init__(self):
        self.__repo = ConferenceRepository()
        self.__md_service = MarkdownService()

    def get_conference_by_id(self, conf_id, session):
        conference = self.__repo.get_by_id(conf_id, session)

        if not conference:
            raise ConferenceNotFoundException(conf_id)
        return conference

    def exists(self, conf_id, session):
        existing = self.__repo.exists(conf_id, session)

        if not existing:
            raise ConferenceNotFoundException(conf_id)
        return existing

    def create_conference(self, conf_data, session):
        # valid_data = self.__convert_and_validate_data(conf_data)
        valid_data = self.__convert_data(conf_data)
        new_conference = Conference()
        self.__fill_conference(new_conference, valid_data)

        description_html = self.__md_service.to_html(new_conference.description_md)
        new_conference.description_html = description_html

        return self.__repo.save(new_conference, session)

    def update_conference(self, conf_id, update_conf_data, session):
        conference = self.get_conference_by_id(conf_id, session)

        valid_data = self.__convert_and_validate_data(update_conf_data)

        self.__fill_conference(conference, valid_data)

        description_html = self.__md_service.to_html(conference.description_md)
        conference.description_html = description_html

        self.__repo.save(conference, session)

    def get_all_conferences(self, session):
        conferences = self.__repo.get_all(session)
        return conferences

    def delete_conference(self, conf_id, session):
        conference = self.__repo.get_by_id(conf_id, session)
        self.__repo.delete(conference, session)

    def get_future_conferences(self, session):
        return self.__repo.get_future_conferences(session)

    def get_past_conferences(self, session):
        return self.__repo.get_past_conferences(session)

    def __fill_conference(self, conference, data):
        for field, value in data.items():
            if hasattr(conference, field):
                setattr(conference, field, value)

    def __convert_data(self, conf_data):
        return {
            "title": conf_data.get("title"),
            "description_md": conf_data.get("description_md"),
            "tagline": conf_data.get("tagline"),
            "performance_time": int(conf_data.get("performance_time")),
            "registration_deadline": datetime.strptime(conf_data.get("registration_deadline"), '%Y-%m-%d').date(),
            "submission_deadline": datetime.strptime(conf_data.get("submission_deadline"), '%Y-%m-%d').date(),
            "start_date": datetime.strptime(conf_data.get("start_date"), '%Y-%m-%d').date(),
            "end_date": datetime.strptime(conf_data.get("end_date"), '%Y-%m-%d').date()
        }

    def __convert_and_validate_data(self, data):
        cleaned_data = self.__clean_data(data)
        self.__check_empty_fields(cleaned_data)

        converted_data = self.__convert_data(cleaned_data)
        self.__validate_dates(converted_data)
        return converted_data

    def __validate_dates(self, data):
        start = data.get('start_date')
        end = data.get('end_date')
        reg_deadline = data.get('registration_deadline')
        thesis_deadline = data.get('submission_deadline')
        program_date = data.get('program_date')

        if start < date.today():
            raise ValidationException(f"Начало конференции ({start}) не может быть в прошлом")

        if end < start:
            raise ValidationException(f"Конец конференции ({end}) не может быть до её начала ({start})")

        if reg_deadline > start or reg_deadline > end:
            raise ValidationException(f"Дедлайн регистрации ({reg_deadline}) должен быть раньше\
                                        даты начала конференции ({start})")

        if thesis_deadline > start:
            raise ValidationException(f"Дедлайн для подачи тезисов ({thesis_deadline}) \
                                        должен быть до начала конференции ({start})")

        if program_date > start or program_date < thesis_deadline:
            raise ValidationException(f"Программа должна публиковаться до начала конференции, \
                                        но после дедлайна на подачу тезисов")

    def __check_empty_fields(self, cleaned_data):
        str_values = ['title', 'description_md']
        for key in str_values:
            if not cleaned_data.get(key):
                raise ValidationException(f"Обязательное поле {key} не может быть пустым")

    def __clean_data(self, data):
        cleaned = {}

        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value

        return cleaned