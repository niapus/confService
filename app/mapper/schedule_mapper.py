from app.dto.dto import ThesisScheduleDTO, ConferenceScheduleDTO, FullScheduleDTO
from app.models.application import Application
from app.models.conference import Conference
from app.models.schedule_item import ScheduleItem
from app.models.thesis import Thesis


class ScheduleMapper:
    """Преобразование моделей конференции и расписания в DTO для редактора расписания."""

    def to_full_schedule_dto(
        self,
        conference: Conference,
        theses_with_applications: list[tuple[Thesis, Application]],
        schedule_items: list[ScheduleItem]
    ) -> FullScheduleDTO:
        return FullScheduleDTO(
            conference=self.__conference_to_schedule_dto(conference),
            applications=[
                self.__thesis_with_application_to_dto(thesis, application)
                for thesis, application in theses_with_applications
            ],
            schedule=[item.to_dict() for item in schedule_items]
        )

    def __thesis_with_application_to_dto(
        self, thesis: Thesis, application: Application
    ) -> ThesisScheduleDTO:
        speaker_name = f"{application.surname} {application.name}"
        if application.patronymic:
            speaker_name += f" {application.patronymic}"
        return ThesisScheduleDTO(
            id=thesis.id,
            speaker_name=speaker_name,
            title=thesis.title
        )

    def __conference_to_schedule_dto(self, conference: Conference) -> ConferenceScheduleDTO:
        return ConferenceScheduleDTO(
            id=conference.id,
            title=conference.title,
            start_date=conference.start_date.strftime('%Y-%m-%d'),
            end_date=conference.end_date.strftime('%Y-%m-%d'),
            performance_time=conference.performance_time
        )
