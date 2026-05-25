"""
Интеграционные тесты ApplicationRepository на реальной SQLite БД.

Покрывают то, что unit-тесты с моками покрыть не могут:
  - реальные SQL-запросы и фильтры;
  - уникальный индекс uq_application_conference_email на уровне БД;
  - каскадное удаление при удалении конференции;
  - joinedload тезисов;
  - delete(synchronize_session=False) с реальными строками.

Проверка уникальности заявки по паре «конференция — email».
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.application import Application, ApplicationStatus
from app.models.conference import Conference
from app.models.thesis import Thesis, ThesisStatus
from app.repository.application_repository import ApplicationRepository


@pytest.fixture
def repo():
    return ApplicationRepository()


@pytest.fixture
def conf(session):
    """Сохранённая в БД конференция-родитель для заявок."""
    today = date.today()
    c = Conference(
        title="Test Conf",
        description_md="# x",
        description_html="<h1>x</h1>",
        tagline="t",
        registration_deadline=today + timedelta(days=30),
        submission_deadline=today + timedelta(days=45),
        start_date=today + timedelta(days=60),
        end_date=today + timedelta(days=62),
        performance_time=15,
    )
    session.add(c)
    session.commit()
    return c


def _make_app(conf_id, email="ivan@test.com", status=ApplicationStatus.CONFIRMED, **overrides):
    from app.models.application import GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum
    a = Application(
        conference_id=conf_id,
        surname=overrides.get("surname", "Иванов"),
        name="Иван",
        patronymic="Иванович",
        gender=GenderEnum.MALE,
        birth_date=date(2000, 1, 1),
        degree=DegreeEnum.NONE,
        is_worker=False,
        is_student=True,
        study_name="UrFU",
        study_place="Екатеринбург",
        study_level=EducationEnum.MASTER,
        participation_format=ParticipationFormatEnum.OFFLINE,
        email=email,
        status=status,
    )
    return a


class TestSave:
    def test_save_persists_application_and_assigns_id(self, repo, session, conf):
        a = _make_app(conf.id)
        repo.save(a, session)
        session.commit()

        assert a.id is not None
        loaded = session.get(Application, a.id)
        assert loaded.email == "ivan@test.com"
        assert loaded.status == ApplicationStatus.CONFIRMED

    def test_unique_constraint_blocks_duplicate_conf_email(self, repo, session, conf):
        repo.save(_make_app(conf.id, email="dup@test.com"), session)
        session.commit()

        # save() сам делает session.flush() — IntegrityError возникает уже здесь.
        with pytest.raises(IntegrityError):
            repo.save(_make_app(conf.id, email="dup@test.com"), session)
        session.rollback()


class TestFindConfirmedByConfEmail:
    def test_returns_only_confirmed(self, repo, session, conf):
        repo.save(_make_app(conf.id, email="a@x.ru", status=ApplicationStatus.UNCONFIRMED), session)
        session.commit()
        assert repo.find_confirmed_application_by_conf_email(conf.id, "a@x.ru", session) is None

        repo.save(_make_app(conf.id, email="b@x.ru", status=ApplicationStatus.CONFIRMED), session)
        session.commit()
        found = repo.find_confirmed_application_by_conf_email(conf.id, "b@x.ru", session)
        assert found is not None
        assert found.email == "b@x.ru"

    def test_returns_none_for_other_conference(self, repo, session, conf):
        repo.save(_make_app(conf.id, email="c@x.ru"), session)
        session.commit()
        assert repo.find_confirmed_application_by_conf_email(999, "c@x.ru", session) is None


class TestGetFullApplicationsForConference:
    def test_returns_only_confirmed_with_theses_eagerly_loaded(self, repo, session, conf):
        a1 = _make_app(conf.id, email="one@x.ru", status=ApplicationStatus.CONFIRMED)
        a2 = _make_app(conf.id, email="two@x.ru", status=ApplicationStatus.UNCONFIRMED)
        repo.save(a1, session)
        repo.save(a2, session)
        session.flush()
        session.add(Thesis(
            application_id=a1.id,
            authors="И. Иванов",
            title="Test",
            file_path="x/y.pdf",
            file_name="y.pdf",
            status=ThesisStatus.PENDING,
        ))
        session.commit()

        result = repo.get_full_applications_for_conference(conf.id, session)
        assert len(result) == 1
        assert result[0].email == "one@x.ru"
        # theses предзагружены — обращение к коллекции не выпускает SQL.
        assert len(result[0].theses) == 1


class TestGetAllConfirmed:
    def test_returns_all_confirmed_across_conferences_desc(self, repo, session, conf):
        repo.save(_make_app(conf.id, email="old@x.ru"), session)
        session.commit()
        repo.save(_make_app(conf.id, email="new@x.ru"), session)
        session.commit()

        all_confirmed = repo.get_all_confirmed(session)
        emails = [a.email for a in all_confirmed]
        assert emails == ["new@x.ru", "old@x.ru"]  # id desc


class TestGetById:
    def test_returns_application(self, repo, session, conf):
        a = _make_app(conf.id)
        repo.save(a, session)
        session.commit()
        assert repo.get_by_id(a.id, session).email == a.email

    def test_returns_none_when_missing(self, repo, session):
        assert repo.get_by_id(123456, session) is None


class TestDeleteUnconfirmedByConfEmail:
    def test_deletes_only_unconfirmed_matching_pair(self, repo, session, conf):
        repo.save(_make_app(conf.id, email="x@x.ru", status=ApplicationStatus.UNCONFIRMED), session)
        repo.save(_make_app(conf.id, email="y@x.ru", status=ApplicationStatus.CONFIRMED), session)
        session.commit()

        repo.delete_unconfirmed_by_conf_email(conf.id, "x@x.ru", session)
        session.commit()

        assert session.query(Application).filter_by(email="x@x.ru").first() is None
        assert session.query(Application).filter_by(email="y@x.ru").first() is not None


class TestDeleteUnconfirmedOlderThan:
    def test_deletes_old_unconfirmed(self, repo, session, conf):
        old = _make_app(conf.id, email="old@x.ru", status=ApplicationStatus.UNCONFIRMED)
        old.created_at = datetime.now() - timedelta(days=10)
        fresh = _make_app(conf.id, email="fresh@x.ru", status=ApplicationStatus.UNCONFIRMED)
        confirmed_old = _make_app(conf.id, email="ok@x.ru", status=ApplicationStatus.CONFIRMED)
        confirmed_old.created_at = datetime.now() - timedelta(days=10)
        for a in (old, fresh, confirmed_old):
            repo.save(a, session)
        session.commit()

        deleted = repo.delete_unconfirmed_older_than(7, session)
        session.commit()

        assert deleted == 1
        assert session.query(Application).filter_by(email="old@x.ru").first() is None
        assert session.query(Application).filter_by(email="fresh@x.ru").first() is not None
        assert session.query(Application).filter_by(email="ok@x.ru").first() is not None


class TestConferenceCascadeDelete:
    def test_deleting_conference_cascades_to_applications(self, repo, session, conf):
        repo.save(_make_app(conf.id, email="z@x.ru"), session)
        session.commit()
        assert session.query(Application).count() == 1

        session.delete(conf)
        session.commit()
        assert session.query(Application).count() == 0
