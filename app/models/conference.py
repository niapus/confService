from sqlalchemy import Column, Integer, String, Text, Date
from sqlalchemy.orm import relationship

from app.core.database import Base


class Conference(Base):
    __tablename__ = "conferences"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)

    description_md = Column(Text, nullable=False)
    description_html = Column(Text, nullable=False)

    tagline = Column(String)

    registration_deadline = Column(Date, nullable=False)
    submission_deadline = Column(Date, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    performance_time = Column(Integer, nullable=False)

    applications = relationship(
        "Application",
        back_populates="conference",
        cascade="all, delete-orphan"
    )

    files = relationship(
        "ConferenceFile",
        back_populates="conference",
        cascade="all, delete-orphan"
    )

    schedule_items = relationship(
        "ScheduleItem",
        back_populates="conference",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'performance_time': self.performance_time
        }