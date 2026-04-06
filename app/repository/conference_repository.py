from app.models.conference import Conference
from sqlalchemy import exists
from datetime import date

class ConferenceRepository:

    def save(self, conference, session):
        session.add(conference)
        return conference

    def get_by_id(self, conference_id, session):
        conference = session.query(Conference).get(conference_id)
        return conference

    def get_all(self, session):
        conferences = session.query(Conference).all()
        return conferences

    def delete(self, conference, session):
        session.delete(conference)

    def exists(self, conf_id, session):
        return session.query(
            exists().where(Conference.id == conf_id)
        ).scalar()

    def get_future_conferences(self, session):
        return session.query(Conference).filter(
            Conference.end_date >= date.today()
        ).order_by(Conference.end_date).all()

    def get_past_conferences(self, session):
        return session.query(Conference).filter(
            Conference.end_date < date.today()
        ).order_by(Conference.end_date.desc()).all()