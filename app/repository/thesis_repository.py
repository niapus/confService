from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.thesis import Thesis, ThesisStatus


class ThesisRepository:
    """Доступ к данным тезисов."""

    def save(self, thesis: Thesis, session: Session) -> Thesis:
        session.add(thesis)
        return thesis

    def get_all(self, session: Session) -> list[Thesis]:
        return session.query(Thesis).order_by(Thesis.id.desc()).all()

    def get_by_id(self, thesis_id: int, session: Session) -> Thesis | None:
        return session.get(Thesis, thesis_id)

    def get_by_conf_id(self, conf_id: int, session: Session) -> list[Thesis]:
        return session.query(Thesis)\
            .join(Application)\
            .filter(Application.conference_id == conf_id)\
            .all()

    def get_accepted_theses_with_applications(
        self, conf_id: int, session: Session
    ) -> list[tuple[Thesis, Application]]:
        """Возвращает принятые тезисы вместе с заявками для указанной конференции."""
        return session.query(Thesis, Application).join(
            Application,
            Thesis.application_id == Application.id
        ).filter(
            Application.conference_id == conf_id,
            Thesis.status == ThesisStatus.ACCEPTED
        ).all()

    def delete_all(self, files: list[Thesis], session: Session) -> None:
        for file in files:
            session.delete(file)
