from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.thesis import Thesis, ThesisStatus


class ThesisRepository:

    def save(self, thesis, session):
        session.add(thesis)
        return thesis

    def get_all(self, session):
        return session.query(Thesis).order_by(Thesis.id.desc()).all()

    def get_by_id(self, thesis_id, session):
        thesis = session.get(Thesis, thesis_id)
        return thesis

    def get_by_conf_id(self, conf_id, session):
        return session.query(Thesis)\
            .join(Application)\
            .filter(Application.conference_id == conf_id)\
            .all()

    def get_accepted_theses_with_applications(self, conf_id, session):
        return session.query(
            Thesis,
            Application
        ).join(
            Application,
            Thesis.application_id == Application.id
        ).filter(
            Application.conference_id == conf_id,
            Thesis.status == ThesisStatus.ACCEPTED
        ).all()

    def delete_all(self, files, session: Session):
        for file in files:
            session.delete(file)
