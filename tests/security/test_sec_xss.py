"""
Защита от межсайтового выполнения сценариев (XSS).

Два уровня защиты:
  1) Jinja2 автоэкранирование — все переменные в шаблонах HTML/XML экранируются
     автоматически, опасные теги превращаются в текстовые сущности.
  2) bleach.clean в MarkdownService — описание конференции хранится как
     Markdown - HTML, и при конверсии санитизируется белым списком тегов
     и атрибутов; javascript: и data:

Тесты гоняют типовые XSS-вектора через MarkdownService
и публичные страницы.
"""
from html.parser import HTMLParser

import pytest

from app.service.markdown_service import MarkdownService


XSS_PAYLOADS_HTML = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<iframe src='javascript:alert(1)'></iframe>",
    "<a href='javascript:alert(1)'>x</a>",
    "<body onload=alert(1)>",
    "<input onfocus=alert(1) autofocus>",
    "<details open ontoggle=alert(1)>",
    "<a href='data:text/html,<script>alert(1)</script>'>x</a>",
    "<object data='javascript:alert(1)'></object>",
    "<form action='javascript:alert(1)'><button>x</button></form>",
    "<style>@import 'javascript:alert(1)';</style>",
]

# Теги, которых не должно остаться как РЕАЛЬНЫХ DOM-элементов.
# Если bleach их экранировал (`&lt;svg&gt;`), это безопасно — браузер увидит текст.
DANGEROUS_TAGS = {
    "script", "iframe", "svg", "body", "input", "details",
    "object", "form", "style", "embed", "link", "meta", "frame", "frameset",
}

# Атрибуты, в которых может оказаться javascript:/data:text/html — реально опасные.
URL_ATTRS = {"href", "src", "action", "data", "formaction",
             "background", "poster", "xlink:href"}

# Опасные URL-схемы — должны быть полностью вычищены из URL-атрибутов.
DANGEROUS_URL_SCHEMES = ("javascript:", "vbscript:", "data:text/html")


class _SecurityHTMLAuditor(HTMLParser):
    """Парсит ВЫХОДНОЙ HTML после bleach и фиксирует:
      - реальные DOM-теги;
      - on*-обработчики на реальных тегах;
      - небезопасные URL-схемы в URL-атрибутах."""

    def __init__(self):
        super().__init__()
        self.tags_seen: list[str] = []
        self.event_handlers: list[tuple[str, str]] = []
        self.bad_urls: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag, attrs):
        self.tags_seen.append(tag.lower())
        for name, value in attrs:
            name_l = (name or "").lower()
            if name_l.startswith("on"):
                self.event_handlers.append((tag, name_l))
            if name_l in URL_ATTRS and value is not None:
                v = value.strip().lower()
                # Относительные URL без схемы (типа "x", "./img.png") безопасны.
                # Опасны только URL с активной схемой javascript:/vbscript:/data:text/html.
                if v.startswith(DANGEROUS_URL_SCHEMES):
                    self.bad_urls.append((tag, name_l, v))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def _audit(html: str) -> _SecurityHTMLAuditor:
    aud = _SecurityHTMLAuditor()
    aud.feed(html)
    aud.close()
    return aud


def _assert_no_dangerous_tags(html: str) -> None:
    aud = _audit(html)
    bad = [t for t in aud.tags_seen if t in DANGEROUS_TAGS]
    assert not bad, f"В DOM остались опасные теги {bad}: {html!r}"


def _assert_no_event_handlers(html: str) -> None:
    aud = _audit(html)
    assert not aud.event_handlers, \
        f"На реальных DOM-тегах нашлись on*-обработчики: {aud.event_handlers}"


def _assert_no_dangerous_url_attrs(html: str) -> None:
    aud = _audit(html)
    assert not aud.bad_urls, f"Небезопасные URL в атрибутах: {aud.bad_urls}"


@pytest.fixture
def md():
    return MarkdownService()


class TestMarkdownSanitization:
    """bleach должен вычистить опасные конструкции."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS_HTML)
    def test_no_active_dangerous_tags(self, md, payload):
        """После санитизации опасные теги либо удалены, либо HTML-экранированы (&lt;...&gt;).
        Браузер не интерпретирует экранированный текст как тег → XSS невозможен."""
        html = md.to_html(payload)
        _assert_no_dangerous_tags(html)
        _assert_no_event_handlers(html)
        _assert_no_dangerous_url_attrs(html)

    def test_iframe_stripped(self, md):
        html = md.to_html("<iframe src='https://example.com'></iframe>")
        assert "<iframe" not in html.lower()

    def test_object_stripped(self, md):
        html = md.to_html("<object data='x'></object>")
        assert "<object" not in html.lower()

    def test_form_stripped(self, md):
        html = md.to_html("<form><input></form>")
        assert "<form" not in html.lower()

    def test_style_tag_stripped(self, md):
        html = md.to_html("<style>body{background:url('javascript:alert(1)')}</style>")
        assert "<style" not in html.lower()

    def test_allowed_link_preserved(self, md):
        html = md.to_html("[example](https://example.com)")
        assert "href=\"https://example.com\"" in html or "href='https://example.com'" in html

    def test_mailto_link_preserved(self, md):
        html = md.to_html("[mail](mailto:user@example.com)")
        assert "mailto:user@example.com" in html

    def test_img_https_preserved(self, md):
        html = md.to_html("![alt](https://example.com/x.png)")
        assert "<img" in html
        assert "https://example.com/x.png" in html


class TestStoredXssThroughConferenceForm:
    """Полный сценарий: админ публикует Markdown с payload → публичная страница
    отдаёт безопасный HTML."""

    @pytest.fixture
    def conf_form(self):
        from datetime import date, timedelta
        today = date.today()
        return {
            "title": "XSS",
            "description_md": "",  # заполняется в каждом тесте
            "tagline": "x",
            "registration_deadline": (today + timedelta(days=10)).isoformat(),
            "submission_deadline": (today + timedelta(days=20)).isoformat(),
            "start_date": (today + timedelta(days=30)).isoformat(),
            "end_date": (today + timedelta(days=31)).isoformat(),
            "performance_time": "15",
        }

    @pytest.mark.parametrize("payload", XSS_PAYLOADS_HTML)
    def test_payload_in_conference_description_sanitized_in_html(
        self, admin_client, conf_form, payload, session
    ):
        form = dict(conf_form, description_md=f"# Заголовок\n\n{payload}\n")
        admin_client.post("/admin/conferences/new", data=form)

        from app.models.conference import Conference
        conf = session.query(Conference).first()
        html = conf.description_html
        _assert_no_dangerous_tags(html)
        _assert_no_event_handlers(html)
        _assert_no_dangerous_url_attrs(html)


class TestReflectedXssThroughForm:
    """Поля формы заявки — surname/name и т.д. — рендерятся через Jinja с
    автоэкранированием. Если кто-то вставит <script> в фамилию, в HTML
    админки должен быть &lt;script&gt;, а не исполняемый тег."""

    def _conf(self, session):
        from datetime import date, timedelta
        from app.models.conference import Conference
        today = date.today()
        c = Conference(
            title="C", description_md="x", description_html="x", tagline="t",
            registration_deadline=today + timedelta(days=10),
            submission_deadline=today + timedelta(days=20),
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=31),
            performance_time=15,
        )
        session.add(c)
        session.commit()
        return c

    def test_xss_in_application_surname_escaped(self, admin_client, session):
        conf = self._conf(session)
        # подаём заявку с XSS в фамилии
        admin_client.post(
            f"/conference/{conf.id}/application",
            data={
                "surname": "<script>alert(1)</script>",
                "name": "Иван",
                "patronymic": "Иванович",
                "gender": "male",
                "birth_date": "2000-01-15",
                "degree": "none",
                "status": "student",
                "study_name": "U",
                "study_place": "E",
                "study_level": "education_mag",
                "participation_format": "offline",
                "email": "xss@test.com",
            },
        )
        resp = admin_client.get("/admin")
        assert resp.status_code == 200
        body = resp.data.decode("utf-8")
        # Сырого <script> в HTML быть НЕ должно — Jinja его экранирует
        assert "<script>alert(1)</script>" not in body
        # А экранированная версия — обычный текст
        assert "&lt;script&gt;" in body or "&lt;script" in body
