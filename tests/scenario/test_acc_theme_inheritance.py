import pytest
from jinja2 import Environment

from app.core.theme import ThemeLoader


@pytest.fixture
def two_level_themes(tmp_path):
    """Создаёт parent + child темы и возвращает (themes_dir, child_name)."""
    themes_dir = tmp_path / "themes"

    parent = themes_dir / "parent"
    (parent / "templates").mkdir(parents=True)
    (parent / "theme.yaml").write_text("name: parent\nparent: null\n", encoding="utf-8")
    (parent / "templates" / "base.html").write_text(
        "PARENT_BASE", encoding="utf-8"
    )
    (parent / "templates" / "partial.html").write_text(
        "PARENT_PARTIAL", encoding="utf-8"
    )

    child = themes_dir / "child"
    (child / "templates").mkdir(parents=True)
    (child / "theme.yaml").write_text(
        "name: child\nparent: parent\n", encoding="utf-8"
    )
    # child переопределяет только base.html
    (child / "templates" / "base.html").write_text(
        "CHILD_BASE", encoding="utf-8"
    )

    return themes_dir, "child"


class TestThemeInheritance:

    def test_chain_contains_child_and_parent(self, two_level_themes, tmp_path):
        themes_dir, active = two_level_themes
        loader = ThemeLoader(themes_dir, active, app_dir=tmp_path / "app")
        assert loader.chain == ["child", "parent"]

    def test_child_overrides_base_html(self, two_level_themes, tmp_path):
        themes_dir, active = two_level_themes
        loader = ThemeLoader(themes_dir, active, app_dir=tmp_path / "app")
        env = Environment(loader=loader.get_jinja_loader())
        rendered = env.get_template("base.html").render()
        assert rendered == "CHILD_BASE"

    def test_missing_in_child_inherits_from_parent(self, two_level_themes, tmp_path):
        """child не содержит partial.html — должен подхватиться от parent."""
        themes_dir, active = two_level_themes
        loader = ThemeLoader(themes_dir, active, app_dir=tmp_path / "app")
        env = Environment(loader=loader.get_jinja_loader())
        rendered = env.get_template("partial.html").render()
        assert rendered == "PARENT_PARTIAL"

    def test_default_theme_has_empty_chain(self, tmp_path):
        """ACTIVE_THEME=default — цепочка пустая, используется только app/templates."""
        loader = ThemeLoader(tmp_path / "themes", "default", app_dir=tmp_path / "app")
        assert loader.chain == []

    def test_cycle_protected(self, tmp_path):
        """Защита от циклов: a→b→a — обработка останавливается."""
        themes_dir = tmp_path / "themes"
        for name, parent in (("a", "b"), ("b", "a")):
            d = themes_dir / name
            (d / "templates").mkdir(parents=True)
            (d / "theme.yaml").write_text(
                f"name: {name}\nparent: {parent}\n", encoding="utf-8"
            )
        loader = ThemeLoader(themes_dir, "a", app_dir=tmp_path / "app")
        # Должно завершиться без бесконечного цикла; chain содержит обоих ровно один раз
        assert sorted(loader.chain) == ["a", "b"]

    def test_static_resolution_prefers_child(self, two_level_themes, tmp_path):
        themes_dir, active = two_level_themes
        # Положим CSS в обе темы
        (themes_dir / "parent" / "static").mkdir()
        (themes_dir / "parent" / "static" / "base.css").write_text("PARENT_CSS")
        (themes_dir / "parent" / "static" / "only_parent.css").write_text("ONLY_P")
        (themes_dir / "child" / "static").mkdir()
        (themes_dir / "child" / "static" / "base.css").write_text("CHILD_CSS")

        loader = ThemeLoader(themes_dir, active, app_dir=tmp_path / "app")
        # child переопределяет
        path = loader.resolve_static("base.css")
        assert path.read_text() == "CHILD_CSS"
        # only_parent.css не переопределён
        path = loader.resolve_static("only_parent.css")
        assert path.read_text() == "ONLY_P"
        # несуществующий
        assert loader.resolve_static("nope.css") is None
