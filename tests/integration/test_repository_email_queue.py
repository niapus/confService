"""
Интеграционные тесты EmailRepository на реальной SQLite.

Email-уведомления: фоновая обработка очереди.
"""
from datetime import datetime, timedelta

import pytest

from app.models.email_queue import EmailQueue, EmailStatus, QueueType
from app.repository.email_repository import EmailRepository


@pytest.fixture
def repo():
    return EmailRepository()


def _make_email(
    subject="Test",
    recipient="user@test.com",
    queue_type=QueueType.INDIVIDUAL,
    status=EmailStatus.PENDING,
    attempts=0,
    created_at=None,
):
    e = EmailQueue(
        subject=subject,
        recipient=recipient,
        html_body="<p>x</p>",
        queue_type=queue_type,
        status=status,
        attempts=attempts,
    )
    if created_at is not None:
        e.created_at = created_at
    return e


class TestSave:
    def test_save_persists_and_assigns_id(self, repo, session):
        e = _make_email()
        repo.save(e, session)
        session.commit()
        assert e.id is not None
        assert e.status == EmailStatus.PENDING


class TestDelete:
    def test_delete_removes_row(self, repo, session):
        e = _make_email()
        repo.save(e, session)
        session.commit()

        repo.delete(e, session)
        session.commit()
        assert session.query(EmailQueue).count() == 0


class TestGetPendingWithLimit:
    def test_returns_only_pending_of_requested_type_sorted_by_created_at(self, repo, session):
        now = datetime.now()
        items = [
            _make_email(subject="ind_old", queue_type=QueueType.INDIVIDUAL,
                        created_at=now - timedelta(minutes=10)),
            _make_email(subject="ind_new", queue_type=QueueType.INDIVIDUAL,
                        created_at=now),
            _make_email(subject="mass", queue_type=QueueType.MASS,
                        created_at=now - timedelta(minutes=5)),
            _make_email(subject="failed_ind", queue_type=QueueType.INDIVIDUAL,
                        status=EmailStatus.FAILED,
                        created_at=now - timedelta(minutes=1)),
        ]
        for e in items:
            repo.save(e, session)
        session.commit()

        result = repo.get_pending_with_limit(10, QueueType.INDIVIDUAL, session)
        subjects = [e.subject for e in result]
        assert subjects == ["ind_old", "ind_new"]

    def test_respects_limit(self, repo, session):
        now = datetime.now()
        for i in range(5):
            repo.save(
                _make_email(subject=f"e{i}", created_at=now + timedelta(seconds=i)),
                session,
            )
        session.commit()

        result = repo.get_pending_with_limit(3, QueueType.INDIVIDUAL, session)
        assert len(result) == 3
        assert [e.subject for e in result] == ["e0", "e1", "e2"]

    def test_mass_queue_separately(self, repo, session):
        repo.save(_make_email(subject="m", queue_type=QueueType.MASS), session)
        repo.save(_make_email(subject="i", queue_type=QueueType.INDIVIDUAL), session)
        session.commit()

        mass = repo.get_pending_with_limit(10, QueueType.MASS, session)
        assert [e.subject for e in mass] == ["m"]


class TestDeleteFailedOlderThan:
    def test_deletes_only_failed_older_than_cutoff(self, repo, session):
        now = datetime.now()
        old_failed = _make_email(subject="old_failed", status=EmailStatus.FAILED,
                                 created_at=now - timedelta(days=40))
        fresh_failed = _make_email(subject="fresh_failed", status=EmailStatus.FAILED,
                                   created_at=now - timedelta(days=5))
        old_pending = _make_email(subject="old_pending", status=EmailStatus.PENDING,
                                  created_at=now - timedelta(days=40))
        for e in (old_failed, fresh_failed, old_pending):
            repo.save(e, session)
        session.commit()

        deleted = repo.delete_failed_older_than(30, session)
        session.commit()

        assert deleted == 1
        remaining = {e.subject for e in session.query(EmailQueue).all()}
        assert remaining == {"fresh_failed", "old_pending"}

    def test_zero_when_nothing_to_delete(self, repo, session):
        repo.save(_make_email(subject="pending", status=EmailStatus.PENDING), session)
        session.commit()
        assert repo.delete_failed_older_than(30, session) == 0
