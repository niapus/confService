from app.dto.dto import ThesisScheduleDTO, ConferenceScheduleDTO, FullScheduleDTO


class ScheduleMapper:

    def to_full_schedule_dto(self, conference, theses_with_applications, schedule_items) -> FullScheduleDTO:
        conference_dto = self.__conference_to_schedule_dto(conference)

        thesis_dtos = []
        for thesis, application in theses_with_applications:
            thesis_dto = self.__thesis_with_applications_to_dto(thesis, application)
            thesis_dtos.append(thesis_dto)

        schedule_dicts = [item.to_dict() for item in schedule_items]

        return FullScheduleDTO(
            conference=conference_dto,
            applications=thesis_dtos,
            schedule=schedule_dicts
        )

    def __thesis_with_applications_to_dto(self, thesis, application):
        speaker_name = f"{application.surname} {application.name}"
        if application.patronymic:
            speaker_name += f" {application.patronymic}"

        return ThesisScheduleDTO(
            id=thesis.id,
            speaker_name=speaker_name,
            title=thesis.title
        )

    def __conference_to_schedule_dto(self, conference):
        return ConferenceScheduleDTO(
            id=conference.id,
            title=conference.title,
            start_date=conference.start_date.strftime('%Y-%m-%d'),
            end_date=conference.end_date.strftime('%Y-%m-%d'),
            performance_time=conference.performance_time
        )