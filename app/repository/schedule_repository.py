from sqlalchemy.orm import Session

from app.models.schedule_item import ScheduleItem


class ScheduleRepository:

    def get_by_conference_id(self, conf_id, session: Session):
        return session.query(ScheduleItem)\
            .filter_by(conference_id=conf_id)\
            .order_by(ScheduleItem.global_order)\
            .all()

    def delete_all_by_conference_id(self, conf_id, session: Session) -> int:
        return session.query(ScheduleItem).filter_by(conference_id=conf_id).delete()

    def create_all(self, schedule_items, session):
        session.add_all(schedule_items)
        return schedule_items