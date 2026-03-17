from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.thesis import Thesis
from sqlalchemy import and_


class ApplicationRepository:

    def save(self, application, session):
        session.add(application)
        session.commit()
        return application

    def find_application_by_conf_email(self, conf_id, email, session: Session):
        application = session.query(Application).filter_by(conference_id=conf_id, email=email).first()
        return application

    def get_full_applications(self, conf_id, session: Session):
        results = session.query(
            Application,
            Thesis
        ).outerjoin(
            Thesis,
            and_(  # объединяем условия через and_
                Thesis.conference_id == Application.conference_id,
                Thesis.email == Application.email
            )
        ).filter(
            Application.conference_id == conf_id
        ).all()

        return results