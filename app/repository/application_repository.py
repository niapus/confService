from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.application import Application, ApplicationStatus
from app.models.schedule_item import ScheduleItem, ScheduleItemType


class ApplicationRepository:
    """Доступ к данным заявок участников."""

    def save(self, application: Application, session: Session) -> Application:
        session.add(application)
        session.flush()
        return application

    def find_confirmed_application_by_conf_email(
        self, conf_id: int, email: str, session: Session
    ) -> Application | None:
        """Возвращает подтверждённую заявку по конференции и email, или None."""
        return session.query(Application)\
            .filter_by(conference_id=conf_id, email=email, status=ApplicationStatus.CONFIRMED)\
            .first()

    def get_full_applications_for_conference(
        self, conf_id: int, session: Session
    ) -> list[Application]:
        """Возвращает подтверждённые заявки конференции с предзагрузкой тезисов."""
        return session.query(Application).options(
            joinedload(Application.theses)
        ).filter(
            Application.conference_id == conf_id,
            Application.status == ApplicationStatus.CONFIRMED
        ).all()

    def get_all_confirmed(self, session: Session) -> list[Application]:
        """Возвращает все подтверждённые заявки с предзагрузкой тезисов."""
        return session.query(Application)\
            .options(joinedload(Application.theses))\
            .filter(Application.status == ApplicationStatus.CONFIRMED)\
            .order_by(Application.id.desc())\
            .all()

    def get_by_id(self, id: int, session: Session) -> Application | None:
        return session.get(Application, id)

    def delete_unconfirmed_by_conf_email(self, conf_id: int, email: str, session: Session) -> None:
        """Удаляет неподтверждённые заявки по конференции и email."""
        session.query(Application).filter_by(
            conference_id=conf_id,
            email=email,
            status=ApplicationStatus.UNCONFIRMED
        ).delete(synchronize_session=False)

    def delete_unconfirmed_older_than(self, days: int, session: Session) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        return session.query(Application).filter(
            Application.status == ApplicationStatus.UNCONFIRMED,
            Application.created_at < cutoff
        ).delete(synchronize_session=False)

    def get_applications_from_schedule(
        self, conf_id: int, session: Session
    ) -> list[Application]:
        """Возвращает участников, включённых в расписание как докладчики."""
        return session.query(Application).join(
            ScheduleItem,
            ScheduleItem.application_id == Application.id
        ).filter(
            Application.conference_id == conf_id,
            ScheduleItem.item_type == ScheduleItemType.TALK
        ).distinct().all()
