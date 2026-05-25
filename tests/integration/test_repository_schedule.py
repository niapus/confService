"""
Интеграционные тесты ScheduleRepository на реальной SQLite.

Расписание конференции.
"""
from datetime import date

import pytest

from app.models.schedule_item import ScheduleItem, ScheduleItemType
from app.repository.schedule_repository import ScheduleRepository


@pytest.fixture
def repo():
    return ScheduleRepository()


def _day_item(conf_id, order=1, title="Day 1"):
    return ScheduleItem(
        conference_id=conf_id,
        item_type=ScheduleItemType.DAY,
        global_order=order,
        day_date=date.today(),
        day_title=title,
        day_start_time="09:00",
    )


def _talk_item(conf_id, order, speaker="И. Иванов", app_id=None):
    return ScheduleItem(
        conference_id=conf_id,
        item_type=ScheduleItemType.TALK,
        global_order=order,
        application_id=app_id,
        talk_speaker=speaker,
        talk_title="Test",
        talk_duration=15,
        start_time="2026-08-01T09:00:00",
        end_time="2026-08-01T09:15:00",
    )


class TestCreateAll:
    def test_create_all_persists_items(self, repo, session, persisted_conference):
        items = [
            _day_item(persisted_conference.id, order=1),
            _talk_item(persisted_conference.id, order=2),
        ]
        repo.create_all(items, session)
        session.commit()

        for it in items:
            assert it.id is not None


class TestGetByConferenceId:
    def test_returns_items_sorted_by_global_order(self, repo, session, persisted_conference):
        items = [
            _talk_item(persisted_conference.id, order=3),
            _day_item(persisted_conference.id, order=1),
            _talk_item(persisted_conference.id, order=2, speaker="II"),
        ]
        repo.create_all(items, session)
        session.commit()

        result = repo.get_by_conference_id(persisted_conference.id, session)
        orders = [i.global_order for i in result]
        assert orders == [1, 2, 3]

    def test_returns_empty_for_unknown_conference(self, repo, session):
        assert repo.get_by_conference_id(9999, session) == []

    def test_isolation_between_conferences(
        self, repo, session, persisted_conference
    ):
        # вторая конференция
        from datetime import timedelta
        from app.models.conference import Conference
        today = date.today()
        c2 = Conference(
            title="C2",
            description_md="x", description_html="x", tagline="t",
            registration_deadline=today + timedelta(days=10),
            submission_deadline=today + timedelta(days=20),
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=31),
            performance_time=15,
        )
        session.add(c2)
        session.commit()

        repo.create_all([_day_item(persisted_conference.id)], session)
        repo.create_all([_day_item(c2.id)], session)
        session.commit()

        assert len(repo.get_by_conference_id(persisted_conference.id, session)) == 1
        assert len(repo.get_by_conference_id(c2.id, session)) == 1


class TestDeleteAllByConferenceId:
    def test_returns_count_and_removes_all(self, repo, session, persisted_conference):
        items = [
            _day_item(persisted_conference.id, order=1),
            _talk_item(persisted_conference.id, order=2),
            _talk_item(persisted_conference.id, order=3, speaker="X"),
        ]
        repo.create_all(items, session)
        session.commit()

        deleted = repo.delete_all_by_conference_id(persisted_conference.id, session)
        session.commit()

        assert deleted == 3
        assert repo.get_by_conference_id(persisted_conference.id, session) == []

    def test_zero_when_nothing_to_delete(self, repo, session):
        assert repo.delete_all_by_conference_id(9999, session) == 0


class TestCascadeOnConferenceDelete:
    def test_schedule_items_removed_with_conference(self, repo, session, persisted_conference):
        repo.create_all([_day_item(persisted_conference.id)], session)
        session.commit()
        assert len(repo.get_by_conference_id(persisted_conference.id, session)) == 1

        session.delete(persisted_conference)
        session.commit()
        assert len(repo.get_by_conference_id(persisted_conference.id, session)) == 0
