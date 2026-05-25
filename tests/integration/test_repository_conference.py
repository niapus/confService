"""
Интеграционные тесты ConferenceRepository на реальной SQLite.

CRUD конференции.
"""
from datetime import date, timedelta

import pytest

from app.models.conference import Conference
from app.repository.conference_repository import ConferenceRepository


@pytest.fixture
def repo():
    return ConferenceRepository()


def _make_conf(title="Test", days_until_start=60, duration=2):
    today = date.today()
    return Conference(
        title=title,
        description_md="# x",
        description_html="<h1>x</h1>",
        tagline="t",
        registration_deadline=today + timedelta(days=days_until_start - 30),
        submission_deadline=today + timedelta(days=days_until_start - 15),
        start_date=today + timedelta(days=days_until_start),
        end_date=today + timedelta(days=days_until_start + duration),
        performance_time=15,
    )


class TestSave:
    def test_save_assigns_id(self, repo, session):
        c = _make_conf()
        repo.save(c, session)
        session.commit()
        assert c.id is not None


class TestGetById:
    def test_returns_conference(self, repo, session):
        c = _make_conf("Find Me")
        repo.save(c, session)
        session.commit()
        assert repo.get_by_id(c.id, session).title == "Find Me"

    def test_returns_none_when_missing(self, repo, session):
        assert repo.get_by_id(9999, session) is None


class TestGetAll:
    def test_returns_all_ordered_by_id_desc(self, repo, session):
        c1 = _make_conf("First")
        c2 = _make_conf("Second")
        repo.save(c1, session)
        session.commit()
        repo.save(c2, session)
        session.commit()

        result = repo.get_all(session)
        assert [c.title for c in result] == ["Second", "First"]


class TestExists:
    def test_returns_true_when_exists(self, repo, session):
        c = _make_conf()
        repo.save(c, session)
        session.commit()
        assert repo.exists(c.id, session) is True

    def test_returns_false_when_missing(self, repo, session):
        assert repo.exists(9999, session) is False


class TestDelete:
    def test_delete_removes_from_db(self, repo, session):
        c = _make_conf()
        repo.save(c, session)
        session.commit()
        cid = c.id

        repo.delete(c, session)
        session.commit()
        assert repo.get_by_id(cid, session) is None


class TestGetFutureConferences:
    def test_returns_only_with_end_date_today_or_future_sorted_asc(self, repo, session):
        past = _make_conf("Past", days_until_start=-30, duration=2)
        future_near = _make_conf("FutureNear", days_until_start=5, duration=2)
        future_far = _make_conf("FutureFar", days_until_start=100, duration=2)
        for c in (past, future_near, future_far):
            repo.save(c, session)
        session.commit()

        result = repo.get_future_conferences(session)
        # end_date ASC; ближайшая первая
        titles = [c.title for c in result]
        assert "Past" not in titles
        assert titles == ["FutureNear", "FutureFar"]


class TestGetPastConferences:
    def test_returns_only_past_sorted_desc(self, repo, session):
        old = _make_conf("Old", days_until_start=-90, duration=2)
        recent = _make_conf("Recent", days_until_start=-10, duration=2)
        future = _make_conf("Future", days_until_start=10, duration=2)
        for c in (old, recent, future):
            repo.save(c, session)
        session.commit()

        result = repo.get_past_conferences(session)
        titles = [c.title for c in result]
        assert "Future" not in titles
        assert titles == ["Recent", "Old"]  # end_date DESC, недавняя первая


class TestGetStartingInDays:
    def test_returns_conferences_starting_in_exact_n_days(self, repo, session):
        c_today = _make_conf("Today", days_until_start=0)
        c_in_1 = _make_conf("InOne", days_until_start=1)
        c_in_2 = _make_conf("InTwo", days_until_start=2)
        c_in_1b = _make_conf("InOneB", days_until_start=1)
        for c in (c_today, c_in_1, c_in_2, c_in_1b):
            repo.save(c, session)
        session.commit()

        result = repo.get_starting_in_days(session, days=1)
        titles = sorted([c.title for c in result])
        assert titles == ["InOne", "InOneB"]
