from app.service.markdown_service import MarkdownService


class TestMarkdownToHtml:
    """Юнит-проверки MarkdownService на уровне приёмки: основные конструкции."""

    def setup_method(self):
        self.md = MarkdownService()

    def test_heading_converted(self):
        html = self.md.to_html("# Заголовок")
        assert "<h1>Заголовок</h1>" in html

    def test_bold_and_italic(self):
        html = self.md.to_html("**bold** and *italic*")
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_list(self):
        html = self.md.to_html("- one\n- two\n- three")
        assert "<ul>" in html and "<li>one</li>" in html

    def test_link_safe(self):
        html = self.md.to_html("[text](https://example.com)")
        assert '<a href="https://example.com">text</a>' in html

    def test_script_tag_stripped(self):
        html = self.md.to_html("# t\n<script>alert(1)</script>\nbody")
        assert "<script>" not in html
        assert "alert(1)" not in html or "<script>" not in html

    def test_javascript_url_stripped(self):
        html = self.md.to_html("[click](javascript:alert(1))")
        assert "javascript:" not in html

    def test_onclick_attribute_stripped(self):
        html = self.md.to_html('<a href="https://x.com" onclick="alert(1)">x</a>')
        assert "onclick" not in html


class TestPublicConferencePage:
    """Markdown сохраняется в БД и попадает на публичную страницу."""

    def test_admin_creates_with_md_and_public_sees_html(self, admin_client, client, app):
        from datetime import date, timedelta
        today = date.today()
        admin_client.post(
            "/admin/conferences/new",
            data={
                "title": "MD Test",
                "description_md": "# Заголовок\n\nЭто **жирный** текст.",
                "tagline": "x",
                "registration_deadline": (today + timedelta(days=10)).isoformat(),
                "submission_deadline": (today + timedelta(days=20)).isoformat(),
                "start_date": (today + timedelta(days=30)).isoformat(),
                "end_date": (today + timedelta(days=31)).isoformat(),
                "performance_time": "15",
            },
        )

        from app.core import database
        from app.models.conference import Conference
        s = database.Session()
        try:
            conf = s.query(Conference).first()
            conf_id = conf.id
            assert "<h1>Заголовок</h1>" in conf.description_html
            assert "<strong>жирный</strong>" in conf.description_html
        finally:
            s.close()

        # Публичная страница содержит ту же HTML-разметку
        client.get("/admin/logout")
        resp = client.get(f"/conference/{conf_id}")
        assert resp.status_code == 200
        body = resp.data.decode("utf-8")
        assert "<h1>Заголовок</h1>" in body
        assert "<strong>жирный</strong>" in body

    def test_xss_attempt_in_md_is_sanitized(self, admin_client, app):
        from datetime import date, timedelta
        today = date.today()
        malicious_md = "# t\n<script>alert(1)</script>\n[link](javascript:alert(2))"
        admin_client.post(
            "/admin/conferences/new",
            data={
                "title": "XSS Test",
                "description_md": malicious_md,
                "tagline": "x",
                "registration_deadline": (today + timedelta(days=10)).isoformat(),
                "submission_deadline": (today + timedelta(days=20)).isoformat(),
                "start_date": (today + timedelta(days=30)).isoformat(),
                "end_date": (today + timedelta(days=31)).isoformat(),
                "performance_time": "15",
            },
        )
        from app.core import database
        from app.models.conference import Conference
        s = database.Session()
        try:
            conf = s.query(Conference).first()
            html = conf.description_html
        finally:
            s.close()

        assert "<script>" not in html
        assert "javascript:" not in html
