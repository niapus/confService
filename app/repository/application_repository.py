from sqlalchemy.orm import Session, joinedload

from app.models.application import Application, ApplicationStatus
from app.models.schedule_item import ScheduleItem, ScheduleItemType


class ApplicationRepository:

    def save(self, application, session):
        session.add(application)
        session.flush()
        return application

    def find_confirmed_application_by_conf_email(self, conf_id, email, session: Session):
        application = session.query(Application)\
            .filter_by(conference_id=conf_id, email=email, status=ApplicationStatus.CONFIRMED)\
            .first()
        return application

    def get_full_applications_for_conference(self, conf_id, session: Session):
        result = session.query(Application).options(
            joinedload(Application.theses)
        ).filter(
            Application.conference_id == conf_id,
            Application.status == ApplicationStatus.CONFIRMED
        ).all()

        return result

    def get_all(self, session):
        return session.query(Application)\
            .options(joinedload(Application.theses))\
            .filter(Application.status == ApplicationStatus.CONFIRMED)\
            .order_by(Application.id.desc())\
            .all()

    def get_by_id(self, id, session):
        return session.query(Application).get(id)

    def get_applications_from_schedule(self, conf_id, session: Session):
        return session.query(Application).join(
            ScheduleItem,
            ScheduleItem.application_id == Application.id
        ).filter(
            Application.conference_id == conf_id,
            ScheduleItem.item_type == ScheduleItemType.TALK
        ).distinct().all()