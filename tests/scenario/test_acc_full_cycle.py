from datetime import date, timedelta
from io import BytesIO

import pytest

from app.models.application import Application, ApplicationStatus
from app.models.conference import Conference
from app.models.thesis import Thesis, ThesisStatus


def _conf_form_data(title="Scenario Conf"):
    """Поля формы создания/редактирования конференции."""
    today = date.today()
    return {
        "title": title,
        "description_md": "# Описание\n\nДемо-конференция",
        "tagline": "Тематика",
        "registration_deadline": (today + timedelta(days=30)).isoformat(),
        "submission_deadline": (today + timedelta(days=45)).isoformat(),
        "start_date": (today + timedelta(days=60)).isoformat(),
        "end_date": (today + timedelta(days=62)).isoformat(),
        "performance_time": "15",
    }


def _application_form_data(email="ivan@test.com"):
    return {
        "surname": "Иванов",
        "name": "Иван",
        "patronymic": "Иванович",
        "gender": "male",
        "birth_date": "2000-01-15",
        "degree": "none",
        "status": "student",  # _lists getlist
        "study_name": "UrFU",
        "study_place": "Екатеринбург",
        "study_level": "education_mag",
        "participation_format": "offline",
        "email": email,
    }


class TestEndToEndFullCycle:
    """Сквозной пользовательский сценарий через все ключевые маршруты."""

    def test_admin_can_login(self, client):
        resp = client.post(
            "/auth/login", data={"login": "admin", "password": "password1234"}
        )
        assert resp.status_code == 302  # успешный вход → редирект

    def test_admin_creates_conference(self, admin_client, app):
        resp = admin_client.post("/admin/conferences/new",
                                 data=_conf_form_data("New Conf"))
        assert resp.status_code in (200, 302)

        from app.core import database
        s = database.Session()
        try:
            confs = s.query(Conference).all()
            assert len(confs) == 1
            assert confs[0].title == "New Conf"
        finally:
            s.close()

    def test_conference_visible_on_public_page(self, admin_client, client, app):
        admin_client.post("/admin/conferences/new",
                          data=_conf_form_data("Visible Conf"))
        # выходим из сессии — публичный посетитель не админ
        client.get("/admin/logout")

        resp = client.get("/")
        assert resp.status_code == 200
        assert "Visible Conf".encode() in resp.data

    def test_participant_submits_application(self, admin_client, client, app):
        admin_client.post("/admin/conferences/new", data=_conf_form_data())
        from app.core import database
        s = database.Session()
        try:
            conf_id = s.query(Conference).first().id
        finally:
            s.close()

        resp = client.post(
            f"/conference/{conf_id}/application",
            data=_application_form_data(),
        )
        assert resp.status_code in (200, 302)

        s = database.Session()
        try:
            apps = s.query(Application).all()
            assert len(apps) == 1
            assert apps[0].email == "ivan@test.com"
            assert apps[0].status == ApplicationStatus.CONFIRMED
        finally:
            s.close()

    def test_participant_uploads_thesis(self, admin_client, client, app, pdf_bytes):
        admin_client.post("/admin/conferences/new", data=_conf_form_data())
        from app.core import database
        s = database.Session()
        try:
            conf_id = s.query(Conference).first().id
        finally:
            s.close()

        client.post(f"/conference/{conf_id}/application",
                    data=_application_form_data())

        resp = client.post(
            f"/conference/{conf_id}/thesis",
            data={
                "authors": "И. Иванов",
                "title": "Test Thesis",
                "email": "ivan@test.com",
                "file": (BytesIO(pdf_bytes), "thesis.pdf"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code in (200, 302)

        s = database.Session()
        try:
            theses = s.query(Thesis).all()
            assert len(theses) == 1
            assert theses[0].title == "Test Thesis"
            assert theses[0].status == ThesisStatus.PENDING
        finally:
            s.close()

    def test_admin_changes_thesis_status_to_accepted(
        self, admin_client, client, app, pdf_bytes
    ):
        admin_client.post("/admin/conferences/new", data=_conf_form_data())
        from app.core import database
        s = database.Session()
        try:
            conf_id = s.query(Conference).first().id
        finally:
            s.close()

        client.post(f"/conference/{conf_id}/application",
                    data=_application_form_data())
        client.post(
            f"/conference/{conf_id}/thesis",
            data={
                "authors": "И. Иванов",
                "title": "Test Thesis",
                "email": "ivan@test.com",
                "file": (BytesIO(pdf_bytes), "thesis.pdf"),
            },
            content_type="multipart/form-data",
        )

        s = database.Session()
        try:
            thesis_id = s.query(Thesis).first().id
        finally:
            s.close()

        # Сделать клиента снова админом
        admin_client.post("/auth/login",
                          data={"login": "admin", "password": "password1234"})
        resp = admin_client.post(
            f"/admin/theses/{thesis_id}/status",
            data={"status": "accepted"},
        )
        assert resp.status_code in (200, 302)

        s = database.Session()
        try:
            assert s.get(Thesis, thesis_id).status == ThesisStatus.ACCEPTED
        finally:
            s.close()