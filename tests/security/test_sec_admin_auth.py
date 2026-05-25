"""
Безопасность аутентификации администратора.

Покрывает:
  - POST /auth/login: правильные → 302 + admin_id в сессии;
  - неверный логин/пароль → AuthException, сессия пустая;
  - admin_bp.before_request: без admin_id любой /admin/* → 403 ForbiddenException;
  - require_admin_api: /api/* без авторизации → JSON 403;
  - logout очищает сессию полностью (не только admin_id);
  - session-cookie: HttpOnly, SameSite=Lax (из Config).
"""
import pytest

from app.config import Config


class TestLoginEndpoint:

    def test_valid_credentials_set_admin_session(self, client):
        resp = client.post("/auth/login", data={"login": "admin", "password": "password1234"})
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess.get("admin_id") is not None
            assert sess.get("admin_login") == "admin"

    def test_invalid_password_does_not_set_session(self, client):
        resp = client.post("/auth/login", data={"login": "admin", "password": "wrong"})
        # 401 (AuthException) с error.html
        assert resp.status_code == 401
        with client.session_transaction() as sess:
            assert sess.get("admin_id") is None

    def test_missing_user_returns_same_error(self, client):
        resp = client.post("/auth/login", data={"login": "nope", "password": "anything"})
        assert resp.status_code == 401
        with client.session_transaction() as sess:
            assert sess.get("admin_id") is None

    def test_empty_credentials_rejected(self, client):
        resp = client.post("/auth/login", data={"login": "", "password": ""})
        assert resp.status_code in (400, 401)
        with client.session_transaction() as sess:
            assert sess.get("admin_id") is None


class TestAdminEndpointsRequireAuth:
    """Любой /admin/* без admin_id → 403."""

    @pytest.mark.parametrize("path", [
        "/admin",
        "/admin/conferences/create",
        "/admin/logs",
    ])
    def test_get_admin_endpoint_anon_returns_403(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 403

    def test_post_admin_endpoint_anon_returns_403(self, client):
        resp = client.post("/admin/conferences/new", data={})
        assert resp.status_code == 403

    def test_admin_logged_in_can_access(self, admin_client):
        resp = admin_client.get("/admin")
        assert resp.status_code == 200


class TestApiEndpointsRequireAuth:
    """JSON 403 без авторизации (require_admin_api), а не HTML."""

    def test_api_log_files_anon(self, client):
        resp = client.get("/api/log-files")
        assert resp.status_code == 403
        assert resp.is_json
        assert resp.get_json()["status_code"] == 403

    def test_api_logs_anon(self, client):
        resp = client.get("/api/logs")
        assert resp.status_code == 403
        assert resp.is_json

    def test_api_schedule_anon_post(self, client):
        resp = client.post("/api/schedule", json={"conference_id": 1, "schedule": []})
        assert resp.status_code == 403

    def test_api_log_files_admin_ok(self, admin_client):
        resp = admin_client.get("/api/log-files")
        assert resp.status_code == 200


class TestLogoutClearsSession:

    def test_logout_clears_admin_id_and_login(self, admin_client):
        with admin_client.session_transaction() as sess:
            assert sess.get("admin_id") is not None

        resp = admin_client.get("/admin/logout")
        assert resp.status_code == 302
        with admin_client.session_transaction() as sess:
            assert sess.get("admin_id") is None
            assert sess.get("admin_login") is None

    def test_after_logout_admin_endpoint_403(self, admin_client):
        admin_client.get("/admin/logout")
        resp = admin_client.get("/admin")
        assert resp.status_code == 403


class TestSessionCookieFlags:
    """Конфигурация cookie должна защищать сессию от JS и CSRF."""

    def test_httponly_default(self):
        assert Config.SESSION_COOKIE_HTTPONLY is True

    def test_samesite_lax_or_strict(self):
        assert Config.SESSION_COOKIE_SAMESITE in ("Lax", "Strict")

    def test_set_cookie_header_is_httponly(self, client):
        resp = client.post("/auth/login", data={"login": "admin", "password": "password1234"})
        set_cookie = resp.headers.get("Set-Cookie", "")
        # session-cookie должна быть HttpOnly
        assert "HttpOnly" in set_cookie or "httponly" in set_cookie.lower()
