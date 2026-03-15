from app.models.conference import Conference

class ConferenceRepository:

    def save(self, conference, session):
        session.add(conference)
        session.commit()
        return conference

    def get_by_id(self, conference_id, session):
        conference = session.query(Conference).get(conference_id)
        return conference

    def get_all(self, session):
        conferences = session.query(Conference).all()
        return conferences

    def delete(self, conference, session):
        session.delete(conference)
        session.commit()