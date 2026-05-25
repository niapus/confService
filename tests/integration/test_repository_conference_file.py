"""
Интеграционные тесты ConferenceFileRepository на реальной SQLite.

Файлы конференции: сборник тезисов и сопутствующие файлы.
"""
import pytest

from app.models.conference_file import ConferenceFile, ConferenceFileType
from app.repository.conference_file_repository import ConferenceFileRepository


@pytest.fixture
def repo():
    return ConferenceFileRepository()


def _make_file(
    conf_id,
    file_type=ConferenceFileType.CONFERENCE_FILE,
    original_name="file.pdf",
    title="Title",
):
    return ConferenceFile(
        conference_id=conf_id,
        file_type=file_type,
        original_name=original_name,
        file_path=f"{conf_id}/files/{original_name}",
        title=title,
    )


class TestSave:
    def test_save_persists_and_assigns_id(self, repo, session, persisted_conference):
        f = _make_file(persisted_conference.id)
        repo.save(f, session)
        session.commit()
        assert f.id is not None


class TestGetById:
    def test_returns_file(self, repo, session, persisted_conference):
        f = _make_file(persisted_conference.id, original_name="x.pdf")
        repo.save(f, session)
        session.commit()
        assert repo.get_by_id(f.id, session).original_name == "x.pdf"

    def test_returns_none_when_missing(self, repo, session):
        assert repo.get_by_id(9999, session) is None


class TestGetAllByConferenceId:
    def test_returns_all_for_conference(self, repo, session, persisted_conference):
        f1 = _make_file(persisted_conference.id, original_name="a.pdf")
        f2 = _make_file(persisted_conference.id, original_name="b.pdf")
        repo.save(f1, session)
        repo.save(f2, session)
        session.commit()

        result = repo.get_all_by_conf_id(persisted_conference.id, session)
        assert {f.original_name for f in result} == {"a.pdf", "b.pdf"}

    def test_empty_for_unknown_conference(self, repo, session):
        assert repo.get_all_by_conf_id(9999, session) == []


class TestDelete:
    def test_delete_removes_row(self, repo, session, persisted_conference):
        f = _make_file(persisted_conference.id)
        repo.save(f, session)
        session.commit()
        fid = f.id

        repo.delete(f, session)
        session.commit()
        assert repo.get_by_id(fid, session) is None


class TestDeleteAll:
    def test_delete_all_removes_all_for_conference(self, repo, session, persisted_conference):
        for i in range(3):
            repo.save(_make_file(persisted_conference.id, original_name=f"f{i}.pdf"), session)
        session.commit()

        repo.delete_all(persisted_conference.id, session)
        session.commit()
        assert repo.get_all_by_conf_id(persisted_conference.id, session) == []


class TestGetProceedings:
    def test_returns_proceedings_only(self, repo, session, persisted_conference):
        proc = _make_file(persisted_conference.id, file_type=ConferenceFileType.PROCEEDINGS,
                          original_name="proc.pdf")
        regular = _make_file(persisted_conference.id, file_type=ConferenceFileType.CONFERENCE_FILE,
                             original_name="reg.pdf")
        repo.save(proc, session)
        repo.save(regular, session)
        session.commit()

        result = repo.get_proceedings(persisted_conference.id, session)
        assert result is not None
        assert result.original_name == "proc.pdf"

    def test_returns_none_without_proceedings(self, repo, session, persisted_conference):
        repo.save(_make_file(persisted_conference.id), session)
        session.commit()
        assert repo.get_proceedings(persisted_conference.id, session) is None


class TestCascadeOnConferenceDelete:
    def test_files_removed_with_conference(self, repo, session, persisted_conference):
        repo.save(_make_file(persisted_conference.id), session)
        session.commit()
        assert len(repo.get_all_by_conf_id(persisted_conference.id, session)) == 1

        session.delete(persisted_conference)
        session.commit()
        assert len(repo.get_all_by_conf_id(persisted_conference.id, session)) == 0
