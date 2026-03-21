from flask import Flask, g
from app.core.database import Base, engine, Session
from app.routes.api import api_bp
from app.routes.conference import conference_bp
from app.routes.admin import admin_bp
from app.routes.main import main_bp
from app.config import Config

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

    Base.metadata.create_all(engine)
    app.register_blueprint(conference_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    return app