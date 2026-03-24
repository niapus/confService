from app.exceptions.validation_exception import ValidationException
from app.exceptions.not_found_exception import ConferenceNotFoundException
from app.repository.conference_repository import ConferenceRepository
from datetime import date
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

    def create_conference(self, conf_dto, session):
        self.__validate_dates(conf_dto)

        new_conference = Conference()
        self.__fill_conference(new_conference, conf_dto)

        return self.__repo.save(new_conference, session)

    def update_conference(self, conf_id, conf_dto, session):
        conference = self.get_conference_by_id(conf_id, session)

        self.__validate_dates(conf_dto)

        self.__fill_conference(conference, conf_dto)

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

    def __fill_conference(self, conference, dto):
        conference.title = dto.title
        conference.tagline = dto.tagline
        conference.registration_deadline = dto.registration_deadline
        conference.submission_deadline = dto.submission_deadline
        conference.start_date = dto.start_date
        conference.end_date = dto.end_date
        conference.performance_time =  dto.performance_time

        self.__update_md_and_html(conference, dto.description_md)

    def __update_md_and_html(self, conference, new_md):
        if conference.description_md != new_md or conference.description_html is None:
            conference.description_html = self.__md_service.to_html(new_md)
        conference.description_md = new_md

    def __validate_dates(self, dto):
        start = dto.start_date
        end = dto.end_date
        reg_deadline = dto.registration_deadline
        thesis_deadline = dto.submission_deadline
        today = date.today()

        if start < today:
            raise ValidationException(f"Начало конференции ({start}) не может быть в прошлом")

        if end < start:
            raise ValidationException(f"Конец конференции ({end}) не может быть до её начала ({start})")

        if reg_deadline >= start:
            raise ValidationException(f"Дедлайн регистрации ({reg_deadline}) должен быть раньше\
                                        даты начала конференции ({start})")

        if thesis_deadline >= start:
            raise ValidationException(f"Дедлайн для подачи тезисов ({thesis_deadline}) \
                                        должен быть до начала конференции ({start})")