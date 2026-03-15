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
        return conference

    def create_conference(self, conf_data, session):
        converted_data = self.__convert_data(conf_data)

        new_conference = Conference()

        for field, value in converted_data.items():
            setattr(new_conference, field, value)

        description_html = self.__md_service.to_html(new_conference.description_md)
        new_conference.description_html = description_html

        return self.__repo.save(new_conference, session)

    def update_conference(self, conf_id, update_conf_data, session):
        conference = self.__repo.get_by_id(conf_id, session)

        if conference:
            conf_data = self.__convert_data(update_conf_data)

            for field, value in conf_data.items():
                setattr(conference, field, value)

            self.__repo.save(conference, session)

    def get_all_conferences(self, session):
        conferences = self.__repo.get_all(session)
        return conferences

    def delete_conference(self, conf_id, session):
        conference = self.__repo.get_by_id(conf_id, session)
        self.__repo.delete(conference, session)


    def __convert_data(self, conf_data):
        conf_data.update({
            "performance_time": int(conf_data.get("performance_time")),
            "registration_deadline": datetime.strptime(conf_data.get("registration_deadline"), '%Y-%m-%d').date(),
            "submission_deadline": datetime.strptime(conf_data.get("submission_deadline"), '%Y-%m-%d').date(),
            "program_date": datetime.strptime(conf_data.get("program_date"), '%Y-%m-%d').date(),
            "start_date": datetime.fromisoformat(conf_data.get("start_date").replace('T', ' ')),
            "end_date": datetime.fromisoformat(conf_data.get("end_date").replace('T', ' '))
        })

        return conf_data