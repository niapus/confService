from sqlalchemy.orm import Session, joinedload
from app.models.application import Application


class ApplicationRepository:

    def save(self, application, session):
        session.add(application)
        return application

    def find_application_by_conf_email(self, conf_id, email, session: Session):
        application = session.query(Application).filter_by(conference_id=conf_id, email=email).first()
        return application

    def get_full_applications_for_conference(self, conf_id, session: Session):
        result = session.query(Application).options(
            joinedload(Application.theses)
        ).filter(
            Application.conference_id == conf_id
        ).all()

        return result

    def get_all(self, session):
        return session.query(Application).all()