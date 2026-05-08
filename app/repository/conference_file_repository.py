from sqlalchemy.orm import Session

from app.models.conference_file import ConferenceFile, ConferenceFileType


class ConferenceFileRepository:
    """Доступ к данным файлов конференций."""

    def save(self, conference_file: ConferenceFile, session: Session) -> ConferenceFile:
        session.add(conference_file)
        return conference_file

    def get_by_id(self, file_id: int, session: Session) -> ConferenceFile | None:
        return session.query(ConferenceFile).filter(ConferenceFile.id == file_id).first()

    def get_all_by_conf_id(self, conf_id: int, session: Session) -> list[ConferenceFile]:
        return session.query(ConferenceFile).filter(ConferenceFile.conference_id == conf_id).all()

    def delete(self, conference_file: ConferenceFile, session: Session) -> None:
        session.delete(conference_file)

    def delete_all(self, conf_id: int, session: Session) -> None:
        session.query(ConferenceFile).filter(
            ConferenceFile.conference_id == conf_id
        ).delete()

    def get_proceedings(self, conf_id: int, session: Session) -> ConferenceFile | None:
        return session.query(ConferenceFile)\
            .filter(
                ConferenceFile.conference_id == conf_id,
                ConferenceFile.file_type == ConferenceFileType.PROCEEDINGS)\
            .first()
