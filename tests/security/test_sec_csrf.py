import pytest


REJECTED = {400, 401, 403, 500}  # любой явный «отказ» — main thing: not 200/302


def _admin_login(client):
    return client.post("/auth/login", data={"login": "admin", "password": "password1234"})


class TestCsrfProtectionEnabled:
    """SeaSurf должен реально проверять токен, когда TESTING=False."""

    def test_login_without_csrf_token_rejected(self, app_csrf_on):
        """Login сам по себе тоже защищён CSRF (csrf.exempt на нём закомментирован)."""
        client = app_csrf_on.test_client()
        resp = _admin_login(client)
        assert resp.status_code in REJECTED, \
            f"Login без CSRF-токена должен быть отклонён, получили {resp.status_code}"
        with client.session_transaction() as sess:
            assert sess.get("admin_id") is None

    def test_post_admin_endpoint_without_token_rejected(self, app_csrf_on):
        """POST /admin/conferences/new без CSRF-токена → отклоняется."""
        client = app_csrf_on.test_client()
        with client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_login"] = "admin"

        resp = client.post("/admin/conferences/new", data={"title": "x"})
        assert resp.status_code in REJECTED
        # ни одна конференция не создалась
        from app.models.conference import Conference
        from app.core import database
        s = database.Session()
        try:
            assert s.query(Conference).count() == 0
        finally:
            s.close()

    def test_post_api_endpoint_without_token_rejected(self, app_csrf_on):
        """POST /api/schedule без токена отклоняется, даже если admin_id в сессии."""
        client = app_csrf_on.test_client()
        with client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_login"] = "admin"
        resp = client.post("/api/schedule", json={"conference_id": 1, "schedule": []})
        assert resp.status_code in REJECTED

    def test_delete_via_post_admin_without_token_rejected(self, app_csrf_on):
        client = app_csrf_on.test_client()
        with client.session_transaction() as sess:
            sess["admin_id"] = 1
            sess["admin_login"] = "admin"
        resp = client.post("/admin/conferences/1/delete", data={})
        assert resp.status_code in REJECTED


class TestCsrfDisabledInTesting:
    """SeaSurf автоматически отключается, когда app.testing == True.
    Это критично — иначе все integration-тесты были бы вынуждены таскать токен."""

    def test_post_admin_passes_without_token_when_testing(self, admin_client):
        resp = admin_client.post("/admin/conferences/new", data={
            "title": "CSRF Off",
            "description_md": "x",
            "tagline": "x",
            "registration_deadline": "2027-01-01",
            "submission_deadline": "2027-01-02",
            "start_date": "2027-01-03",
            "end_date": "2027-01-04",
            "performance_time": "15",
        })
        assert resp.status_code != 403


class TestCsrfTokenInForms:
    """Все state-changing формы шаблонов должны нести скрытое поле csrf_token."""

    @pytest.mark.parametrize("template_path,form_must_have_csrf", [
        ("app/templates/admin-login.html", True),
        ("app/templates/admin.html", True),
        ("app/templates/conference_form.html", True),
        ("app/templates/application.html", True),
        ("app/templates/thesis.html", True),
    ])
    def test_template_has_csrf_token(self, template_path, form_must_have_csrf):
        from app.config import Config
        full = Config.BASE_DIR / template_path
        text = full.read_text(encoding="utf-8")
        if form_must_have_csrf:
            # шаблон должен содержать вызов csrf_token() или CSRF-поле
            assert "csrf_token" in text, f"{template_path} без csrf_token"
