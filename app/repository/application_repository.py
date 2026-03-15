from sqlalchemy.orm import Session
from app.models.application import Application

class ApplicationRepository:

    def save(self, application, session):
        session.add(application)
        session.commit()
        return application

    def find_application_by_conf_email(self, conf_id, email, session: Session):
        application = session.query(Application).filter_by(conference_id=conf_id, email=email).first()
        return application