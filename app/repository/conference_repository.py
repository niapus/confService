from datetime import date, timedelta

from sqlalchemy import exists
from sqlalchemy.orm import Session

from app.models.conference import Conference


class ConferenceRepository:
    """Доступ к данным конференций."""

    def save(self, conference: Conference, session: Session) -> Conference:
        session.add(conference)
        session.flush()
        return conference

    def get_by_id(self, conference_id: int, session: Session) -> Conference | None:
        return session.query(Conference).get(conference_id)

    def get_all(self, session: Session) -> list[Conference]:
        return session.query(Conference).order_by(Conference.id.desc()).all()

    def delete(self, conference: Conference, session: Session) -> Conference:
        session.delete(conference)
        return conference

    def exists(self, conf_id: int, session: Session) -> bool:
        return session.query(
            exists().where(Conference.id == conf_id)
        ).scalar()

    def get_future_conferences(self, session: Session) -> list[Conference]:
        return session.query(Conference).filter(
            Conference.end_date >= date.today()
        ).order_by(Conference.end_date).all()

    def get_past_conferences(self, session: Session) -> list[Conference]:
        return session.query(Conference).filter(
            Conference.end_date < date.today()
        ).order_by(Conference.end_date.desc()).all()

    def get_starting_in_days(self, session: Session, days: int) -> list[Conference]:
        target = date.today() + timedelta(days=days)
        return session.query(Conference).filter(
            Conference.start_date == target
        ).all()
