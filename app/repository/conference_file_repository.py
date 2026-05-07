from sqlalchemy.orm import Session

from app.models.conference_file import ConferenceFile, ConferenceFileType


class ConferenceFileRepository:
    def save(self, conference_file, session):
        session.add(conference_file)
        return conference_file

    def get_by_id(self, file_id, session):
        return session.query(ConferenceFile).filter(ConferenceFile.id == file_id).first()

    def get_all_by_conf_id(self, conf_id, session):
        return session.query(ConferenceFile).filter(ConferenceFile.conference_id == conf_id).all()

    def delete(self, conference_file, session):
        session.delete(conference_file)

    def delete_all(self, conf_id, session: Session):
        session.query(ConferenceFile).filter(
            ConferenceFile.conference_id == conf_id
        ).delete()

    def get_proceedings(self, conf_id, session):
        return session.query(ConferenceFile)\
            .filter(
                ConferenceFile.conference_id == conf_id,
                ConferenceFile.file_type == ConferenceFileType.PROCEEDINGS)\
            .first()