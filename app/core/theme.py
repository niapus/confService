from functools import cached_property
from pathlib import Path

import yaml
from flask import send_from_directory
from jinja2 import FileSystemLoader, ChoiceLoader


class ThemeLoader:
    """
    Система тем оформления для Flask, вдохновлённая Nikola.

    Каждая тема — это папка внутри themes/<имя_темы>/ (корень проекта), содержащая:
      - theme.yaml   : метаданные (name, parent, description)
      - templates/   : шаблоны Jinja2 (для производной темы — только переопределяемые)
      - static/      : CSS, JS, картинки (для производной темы — только переопределяемые)

    Принцип наследования: производная тема содержит ТОЛЬКО те файлы, которые она
    хочет переопределить. Остальные файлы автоматически берутся из родительской темы.

    Пример: тема "dark" наследуется от "default" и содержит только base.html
    и css/base.css. Все остальные шаблоны и стили подхватываются из default.

    Цепочка поиска: дочерняя тема -> родительская тема -> ... -> корневая тема
    """

    def __init__(self, themes_dir: str | Path, active_theme: str, app_dir: str | Path):
        """
        themes_dir  — путь к папке themes/ (корень проекта)
        active_theme — имя активной темы (из Config.ACTIVE_THEME)
        app_dir     — путь к папке app/ (для fallback на app/templates/ и app/static/)
        """
        self.themes_dir = Path(themes_dir)
        self.app_dir = Path(app_dir)
        self.active_theme = active_theme
        self._chain = self._build_chain()

    def _build_chain(self) -> list[str]:
        """
        Построить цепочку наследования тем: от текущей (дочерней) до корневой.

        Если ACTIVE_THEME=default — используем только базовую тему (пустая цепочка).
        Иначе читаем theme.yaml у каждой темы и идём по полю parent вверх по цепочке.
        Защита от циклов: если тема уже встречалась — останавливаемся.

        Пример результата для темы "dark" (parent: default):
            ["dark"]
        """
        # Если тема default — используем только базовые файлы app/templates/ и app/static/
        if self.active_theme == "default":
            return []

        chain = []
        current = self.active_theme
        visited = set()

        while current and current not in visited:
            visited.add(current)
            chain.append(current)

            meta_path = self.themes_dir / current / "theme.yaml"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f) or {}
                    current = meta.get("parent")
            else:
                break

        return chain

    @cached_property
    def chain(self) -> list[str]:
        """Вернуть цепочку наследования (кешируется после первого вызова)."""
        return self._chain

    def get_jinja_loader(self) -> ChoiceLoader:
        """
        Создать Jinja2-загрузчик, который ищет шаблоны по цепочке тем:
        дочерняя -> родительская -> ... -> app/templates/ (fallback).

        ChoiceLoader перебирает загрузчики по порядку: первый найденный файл
        выигрывает. Так дочерняя тема переопределяет шаблоны родительской.
        """
        loaders = []
        for theme_name in self.chain:
            template_dir = self.themes_dir / theme_name / "templates"
            if template_dir.exists():
                loaders.append(FileSystemLoader(str(template_dir)))

        # Fallback: оригинальная папка app/templates/ (обратная совместимость)
        app_templates = self.app_dir / "templates"
        if app_templates.exists():
            loaders.append(FileSystemLoader(str(app_templates)))

        return ChoiceLoader(loaders)

    def resolve_static(self, filename: str) -> Path | None:
        """
        Найти статический файл (CSS/JS/картинка) по цепочке тем.

        Ищет по порядку: дочерняя тема -> родительская -> ... -> app/static/.
        Возвращает путь к первому найденному файлу (дочерний переопределяет родительский).
        Если файл нигде не найден — возвращает None.
        """
        for theme_name in self.chain:
            file_path = self.themes_dir / theme_name / "static" / filename
            if file_path.exists():
                return file_path

        # Fallback: оригинальная папка app/static/
        app_static = self.app_dir / "static" / filename
        if app_static.exists():
            return app_static

        return None

    def get_theme_meta(self, theme_name: str | None = None) -> dict:
        """Прочитать метаданные темы из theme.yaml (name, parent, description)."""
        theme_name = theme_name or self.active_theme
        meta_path = self.themes_dir / theme_name / "theme.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {"name": theme_name, "parent": None}

    def list_themes(self) -> list[dict]:
        """Вернуть список всех доступных тем с их метаданными."""
        themes = []
        if not self.themes_dir.exists():
            return themes
        for item in sorted(self.themes_dir.iterdir()):
            if item.is_dir() and (item / "theme.yaml").exists():
                meta = self.get_theme_meta(item.name)
                meta["dirname"] = item.name
                themes.append(meta)
        return themes

    def setup_app(self, app):
        """
        Подключить систему тем к Flask-приложению. Делает три вещи:

        1. ЗАГРУЗЧИК ШАБЛОНОВ: заменяет app.jinja_loader на ChoiceLoader,
           который ищет шаблоны по цепочке тем (дочерняя -> родительская -> fallback).

        2. РАЗДАЧА СТАТИКИ: подменяет функцию обработки /static/<filename>,
           чтобы Flask искал файлы сначала в папках темы, потом в app/static/.

        3. КОНТЕКСТ ШАБЛОНОВ: добавляет в каждый шаблон переменные:
           {{ theme }}         — словарь с метаданными активной темы
           {{ active_theme }}  — строка с именем активной темы
        """
        # 1. Подменяем загрузчик шаблонов Jinja2
        app.jinja_loader = self.get_jinja_loader()

        # 2. Подменяем раздачу статики
        original_send_static_file = app.send_static_file

        def themed_send_static_file(filename):
            resolved = self.resolve_static(filename)
            if resolved is not None:
                return send_from_directory(str(resolved.parent), resolved.name)
            return original_send_static_file(filename)

        app.send_static_file = themed_send_static_file

        # Подменяем view-функцию маршрута /static/
        app.view_functions["static"] = themed_send_static_file

        # 3. Добавляем информацию о теме в контекст всех шаблонов.
        cached_theme = {
            "theme": self.get_theme_meta(),
            "active_theme": self.active_theme,
        }

        @app.context_processor
        def inject_theme():
            return cached_theme