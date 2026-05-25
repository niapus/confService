"""
Интеграционные тесты ThesisRepository на реальной SQLite.

Приём тезисов: хранение + привязка к заявке + статус.
"""
import pytest

from app.models.thesis import Thesis, ThesisStatus
from app.repository.thesis_repository import ThesisRepository


@pytest.fixture
def repo():
    return ThesisRepository()


def _make_thesis(app_id, title="Test Thesis", status=ThesisStatus.PENDING):
    return Thesis(
        application_id=app_id,
        authors="И. Иванов",
        title=title,
        file_path=f"{app_id}/theses/test.pdf",
        file_name="test.pdf",
        status=status,
    )


class TestSave:
    def test_save_persists_and_assigns_id(self, repo, session, persisted_application):
        t = _make_thesis(persisted_application.id)
        repo.save(t, session)
        session.commit()
        assert t.id is not None


class TestGetById:
    def test_returns_thesis(self, repo, session, persisted_application):
        t = _make_thesis(persisted_application.id, title="Найди")
        repo.save(t, session)
        session.commit()
        assert repo.get_by_id(t.id, session).title == "Найди"

    def test_returns_none_when_missing(self, repo, session):
        assert repo.get_by_id(9999, session) is None


class TestGetAll:
    def test_returns_all_ordered_by_id_desc(self, repo, session, persisted_application):
        t1 = _make_thesis(persisted_application.id, title="A")
        repo.save(t1, session)
        session.commit()
        t2 = _make_thesis(persisted_application.id, title="B")
        repo.save(t2, session)
        session.commit()

        result = repo.get_all(session)
        assert [t.title for t in result] == ["B", "A"]


class TestGetByConferenceId:
    def test_returns_theses_for_conference(self, repo, session, persisted_application):
        t1 = _make_thesis(persisted_application.id, title="A")
        t2 = _make_thesis(persisted_application.id, title="B")
        repo.save(t1, session)
        repo.save(t2, session)
        session.commit()

        result = repo.get_by_conf_id(persisted_application.conference_id, session)
        assert {t.title for t in result} == {"A", "B"}

    def test_empty_for_unknown_conference(self, repo, session):
        assert repo.get_by_conf_id(9999, session) == []


class TestGetAcceptedThesesWithApplications:
    def test_returns_tuples_only_for_accepted(self, repo, session, persisted_application):
        accepted = _make_thesis(persisted_application.id, title="A", status=ThesisStatus.ACCEPTED)
        pending = _make_thesis(persisted_application.id, title="P", status=ThesisStatus.PENDING)
        rejected = _make_thesis(persisted_application.id, title="R", status=ThesisStatus.REJECTED)
        for t in (accepted, pending, rejected):
            repo.save(t, session)
        session.commit()

        result = repo.get_accepted_theses_with_applications(
            persisted_application.conference_id, session
        )
        assert len(result) == 1
        thesis, app_obj = result[0]
        assert thesis.title == "A"
        assert app_obj.id == persisted_application.id


class TestDeleteAll:
    def test_delete_all_removes_listed_theses(self, repo, session, persisted_application):
        t1 = _make_thesis(persisted_application.id, title="A")
        t2 = _make_thesis(persisted_application.id, title="B")
        repo.save(t1, session)
        repo.save(t2, session)
        session.commit()

        repo.delete_all([t1], session)
        session.commit()

        remaining = [t.title for t in repo.get_all(session)]
        assert remaining == ["B"]


class TestCascadeOnApplicationDelete:
    def test_theses_removed_with_application(self, repo, session, persisted_application):
        repo.save(_make_thesis(persisted_application.id), session)
        session.commit()
        assert len(repo.get_all(session)) == 1

        session.delete(persisted_application)
        session.commit()
        assert len(repo.get_all(session)) == 0
