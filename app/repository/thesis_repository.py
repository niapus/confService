from app.models.application import Application
from app.models.thesis import Thesis

class ThesisRepository:

    def save(self, thesis, session):
        session.add(thesis)
        return thesis

    def get_all(self, session):
        return session.query(Thesis).all()

    def get_by_id(self, thesis_id, session):
        thesis = session.get(Thesis, thesis_id)
        return thesis

    def get_by_conf_id(self, conf_id, session):
        return session.query(Thesis)\
            .join(Application)\
            .filter(Application.conference_id == conf_id)\
            .all()