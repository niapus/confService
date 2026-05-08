from sqlalchemy.orm import Session

from app.models.schedule_item import ScheduleItem


class ScheduleRepository:
    """Доступ к данным расписания конференций."""

    def get_by_conference_id(self, conf_id: int, session: Session) -> list[ScheduleItem]:
        return session.query(ScheduleItem)\
            .filter_by(conference_id=conf_id)\
            .order_by(ScheduleItem.global_order)\
            .all()

    def delete_all_by_conference_id(self, conf_id: int, session: Session) -> int:
        """Удаляет все элементы расписания конференции. Возвращает количество удалённых строк."""
        return session.query(ScheduleItem).filter_by(conference_id=conf_id).delete()

    def create_all(self, schedule_items: list[ScheduleItem], session: Session) -> list[ScheduleItem]:
        session.add_all(schedule_items)
        return schedule_items
