from sqlalchemy.orm import Session

from app.dto.dto import ScheduleDTO, ScheduleItemDTO, FullScheduleDTO
from app.mapper.schedule_mapper import ScheduleMapper
from app.models.schedule_item import ScheduleItem
from app.repository.schedule_repository import ScheduleRepository
from app.service.conference_service import ConferenceService
from app.service.notification_service import NotificationService
from app.service.thesis_service import ThesisService


class ScheduleService:
    """Управление расписанием конференции: чтение, создание и уведомление участников."""

    def __init__(
        self,
        conf_service: ConferenceService,
        thesis_service: ThesisService,
        schedule_mapper: ScheduleMapper,
        schedule_repository: ScheduleRepository,
        notification: NotificationService
    ) -> None:
        self.__conf_service = conf_service
        self.__thesis_service = thesis_service
        self.__mapper = schedule_mapper
        self.__repo = schedule_repository
        self.__notification = notification

    def get_full_schedule_data(self, conf_id: int, session: Session) -> FullScheduleDTO:
        """Возвращает полные данные для редактора расписания: конференция, тезисы, расписание."""
        conference = self.__conf_service.get_conference_by_id(conf_id, session)
        theses_applications = self.__thesis_service.get_accepted_theses_with_applications(conf_id, session)
        schedule = self.get_schedule(conf_id, session)
        return self.__mapper.to_full_schedule_dto(conference, theses_applications, schedule)

    def get_schedule(self, conf_id: int, session: Session) -> list[ScheduleItem]:
        """Возвращает элементы расписания конференции в порядке global_order."""
        return self.__repo.get_by_conference_id(conf_id, session)

    def update_schedule(self, schedule_dto: ScheduleDTO, conf_id: int, session: Session) -> None:
        """Заменяет расписание конференции. Уведомляет участников об изменении или публикации."""
        conference = self.__conf_service.get_conference_by_id(conf_id, session)
        deleted_count = self.__repo.delete_all_by_conference_id(conf_id, session)

        items = [self._fill_schedule_item(item, conf_id) for item in schedule_dto.schedule]
        self.__repo.create_all(items, session)

        if deleted_count > 0:
            self.__notification.send_schedule_updated(conference.confirmed_applications, conference, session)
        else:
            self.__notification.send_schedule_published(conference.confirmed_applications, conference, session)

    def _fill_schedule_item(self, item_dto: ScheduleItemDTO, conf_id: int) -> ScheduleItem:
        """Создаёт ORM-объект ScheduleItem из DTO элемента расписания."""
        return ScheduleItem(
            conference_id=conf_id,
            item_type=item_dto.item_type,
            global_order=item_dto.global_order,
            day_date=item_dto.day_date,
            day_title=item_dto.day_title,
            day_start_time=item_dto.day_start_time,
            application_id=item_dto.application_id,
            talk_speaker=item_dto.talk_speaker,
            talk_title=item_dto.talk_title,
            talk_duration=item_dto.talk_duration,
            break_title=item_dto.break_title,
            break_duration=item_dto.break_duration,
            text_content=item_dto.text_content,
            start_time=item_dto.start_time,
            end_time=item_dto.end_time
        )
