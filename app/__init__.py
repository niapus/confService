from flask import Flask, g, render_template
from app.core.database import Base, engine, Session, init_db
from app.exceptions import AppException
from app.exceptions.auth_exception import AuthException
from app.exceptions.not_found_exception import NotFoundException
from app.models.admin import Admin
from app.routes.api import api_bp
from app.routes.auth import auth_bp
from app.routes.conference import conference_bp
from app.routes.admin import admin_bp
from app.routes.main import main_bp
from app.config import Config
from app.service import admin_service

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.before_request
    def before_request():
        g.db = Session()

    @app.teardown_request
    def teardown_db(error):
        db = g.pop('db', None)

        if db is not None:
            if error:
                db.rollback()
            else:
                db.commit()
            db.close()

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error={
            'status_code': 404,
            'message': 'Страница не найдена'
        }), 404

    @app.errorhandler(AppException)
    def handle_custom_error(error):
        return render_template(
            "error.html",
            error=error
        ), error.status_code

    # @app.errorhandler(Exception)
    # def handle_unexpected(error):
    #     return render_template(
    #         "error.html",
    #         error={'status_code': 500, 'message': "Внутренняя ошибка сервера"}
    #     ), 500

    init_db()
    __create_admin()

    app.register_blueprint(auth_bp)
    app.register_blueprint(conference_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    return app

def __create_admin():
    session = Session()
    admin_service.create_default_admin(
        login=Config.ADMIN_LOGIN,
        password=Config.ADMIN_PASSWORD,
        session=session
    )