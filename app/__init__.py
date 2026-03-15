from flask import Flask
from app.core.database import Base, engine
from app.routes.conference import conference_bp
from app.routes.admin import admin_bp
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    Base.metadata.create_all(engine)
    app.register_blueprint(conference_bp)
    app.register_blueprint(admin_bp)

    return app