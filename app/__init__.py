
from babel.dates import format_date
from flask import Flask, g, render_template, request, session as flask_session
from flask_seasurf import SeaSurf

from app.app_services import AppServices
from app.config import Config
from app.core import database
from app.core.database import Base, engine, init_engine
from app.core.startup import init_app
from app.core.theme import ThemeLoader
from app.exceptions import AppException
from app.exceptions.auth_exception import AuthException
from app.exceptions.not_found_exception import NotFoundException
from app.models.admin import Admin
from app.routes.admin import admin_bp
from app.routes.api import api_bp
from app.routes.auth import auth_bp
from app.routes.conference import conference_bp
from app.routes.main import main_bp


_scheduler_lock_fd = None


def _try_start_scheduler(app, worker_id: str) -> None:
    global _scheduler_lock_fd
    try:
        import fcntl
        try:
            f = open('/tmp/scheduler.lock', 'w')
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            _scheduler_lock_fd = f  # удерживаем дескриптор — лок живёт вместе с процессом
            from app.core.scheduler import SchedulerService
            SchedulerService(app).start()
            app.logger.info(f"Планировщик запущен в воркере {worker_id}")
        except (IOError, OSError):
            app.logger.info(f"Планировщик НЕ запущен в воркере {worker_id}")
    except ImportError:
        # Windows — fcntl недоступен, всегда один процесс
        from app.core.scheduler import SchedulerService
        SchedulerService(app).start()
        app.logger.info(f"Планировщик запущен (Windows, воркер {worker_id})")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_engine(app)

    # CSRF protection
    csrf = SeaSurf(app)

    services = AppServices(app)
    app.extensions['services'] = services

    # Theme system
    theme_loader = ThemeLoader(
        app.config.get("THEMES_FOLDER"),
        app.config.get("ACTIVE_THEME"),
        app_dir=app.config.get("BASE_DIR") / 'app'
    )

    theme_loader.setup_app(app)
    app.extensions['theme_loader'] = theme_loader

    init_app(app)

    @app.before_request
    def before_request():
        g.db = database.Session()

    @app.teardown_request
    def teardown_db(error):
        db = g.pop('db', None)

        if db is not None:
            if error or g.get("_has_error", False):
                db.rollback()
            else:
                db.commit()
            db.close()

    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f"404: {request.url}")
        return render_template('error.html', error={
            'status_code': 404,
            'message': 'Страница не найдена'
        }), 404

    @app.errorhandler(AuthException)
    def handle_auth_exception(error):
        app.logger.warning(
            f"Ошибка аутентификации: {error.message} (код: {error.status_code})\n"
            f"URL: {request.url}\n"
            f"Method: {request.method}\n"
            f"IP: {request.remote_addr}"
        )

        return render_template(
            "error.html",
            error=error
        ), error.status_code

    @app.errorhandler(AppException)
    def handle_custom_error(error):
        return render_template(
            "error.html",
            error=error
        ), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if flask_session.get("admin_id"):
            admin_str = f"id={flask_session.get('admin_id')}, login={flask_session.get('admin_login')}"
        else:
            admin_str = "Не авторизован"

        app.logger.error(
            f"Необработанное исключение: {error}\n"
            f"URL: {request.url}\n"
            f"Method: {request.method}\n"
            f"Admin: {admin_str}",
            exc_info=True
        )

        return render_template(
            "error.html",
            error={'status_code': 500, 'message': "Внутренняя ошибка сервера"}
        ), 500

    @app.template_filter('ru_date')
    def ru_date(value, fmt='d MMM y'):
        return format_date(value, format=fmt, locale='ru')

    @app.template_filter('format_time')
    def format_time(value):
        from datetime import datetime
        if not value:
            return ''
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            dt = dt.astimezone()
            return dt.strftime('%H:%M')
        except:
            return value

    app.register_blueprint(auth_bp)
    app.register_blueprint(conference_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    csrf.exempt(app.view_functions['auth.admin_login'])
    csrf.exempt(app.view_functions['conference.create_application'])
    csrf.exempt(app.view_functions['conference.upload_thesis'])

    import os
    worker_id = os.environ.get('WORKER_ID', '0')

    if app.config.get('MAIL_ENABLED'):
        _try_start_scheduler(app, worker_id)

    return app