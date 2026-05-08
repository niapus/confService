import enum
from typing import Any

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class ScheduleItemType(enum.Enum):
    """Тип элемента расписания: день, доклад, перерыв или текстовый блок."""

    DAY = "day"
    TALK = "talk"
    BREAK = "break"
    TEXT = "text"


class ScheduleItem(Base):
    """Элемент программы конференции. Структура полей зависит от типа элемента."""

    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey("conferences.id", ondelete="CASCADE"), nullable=False, index=True)

    item_type = Column(Enum(ScheduleItemType), nullable=False)
    global_order = Column(Integer, nullable=False)

    day_date = Column(Date, nullable=True)
    day_title = Column(String(200), nullable=True)
    day_start_time = Column(String(5), nullable=True)

    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True, index=True)
    talk_speaker = Column(String(200), nullable=True)
    talk_title = Column(String(300), nullable=True)
    talk_duration = Column(Integer, nullable=True)

    break_title = Column(String(100), nullable=True)
    break_duration = Column(Integer, nullable=True)

    text_content = Column(Text, nullable=True)

    start_time = Column(String(25), nullable=True)
    end_time = Column(String(25), nullable=True)

    conference = relationship("Conference", back_populates="schedule_items")

    def to_dict(self) -> dict[str, Any]:
        result = {
            'id': self.id,
            'item_type': self.item_type.value if self.item_type else None,
            'global_order': self.global_order,
        }

        if self.item_type == ScheduleItemType.DAY:
            result.update({
                'day_date': self.day_date.isoformat() if self.day_date else None,
                'day_title': self.day_title,
                'day_start_time': self.day_start_time,
            })
        elif self.item_type == ScheduleItemType.TALK:
            result.update({
                'application_id': self.application_id,
                'talk_speaker': self.talk_speaker,
                'talk_title': self.talk_title,
                'talk_duration': self.talk_duration,
                'start_time': self.start_time,
                'end_time': self.end_time,
            })
        elif self.item_type == ScheduleItemType.BREAK:
            result.update({
                'break_title': self.break_title,
                'break_duration': self.break_duration,
                'start_time': self.start_time,
                'end_time': self.end_time,
            })
        elif self.item_type == ScheduleItemType.TEXT:
            result.update({
                'text_content': self.text_content,
            })

        return result
