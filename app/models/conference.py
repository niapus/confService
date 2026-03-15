from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.application import Application
from app.models.thesis import Thesis


class Conference(Base):
    __tablename__ = "conferences"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    description_md = Column(Text, nullable=False)
    description_html = Column(Text, nullable=False)

    tagline = Column(String)

    registration_deadline = Column(Date, nullable=False)
    submission_deadline = Column(Date, nullable=False)
    program_date = Column(Date, nullable=False)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    performance_time = Column(Integer, nullable=False)

    applications = relationship(
        "Application",
        backref="conference",
        cascade="all, delete-orphan"
    )

    theses = relationship(
        "Thesis",
        backref="conference",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"Конференция: id {self.id} название {self.title}"
