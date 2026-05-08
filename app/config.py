import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent

    LOGS_FOLDER = os.path.join(BASE_DIR, "logs")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    THEMES_FOLDER = BASE_DIR / 'themes'
    ACTIVE_THEME = os.environ.get('ACTIVE_THEME', 'default')

    SQLALCHEMY_DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'sqlite:///data/conference_service.db'
    )

    THESIS_CONTENT_LENGTH = 16 * 1024 * 1024
    PROCEEDINGS_CONTENT_LENGTH = 50 * 1024 * 1024
    CONFERENCE_FILE_CONTENT_LENGTH = 50 * 1024 * 1024

    THESIS_ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
    PROCEEDINGS_ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}
    CONFERENCE_FILE_ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "ppt", "pptx",
                                          "jpg", "jpeg", "png", "zip"}

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_SAMESITE = 'Lax'

    CSRF_COOKIE_NAME = 'csrf_token'

    ADMIN_DATA = os.environ.get('ADMIN_DATA')
    SECRET_KEY = os.environ.get('SECRET_KEY')

    MAIL_ENABLED = os.environ.get('MAIL_ENABLED', 'false').lower() == 'true'
    EMAIL_VERIFICATION_ENABLED = os.environ.get('EMAIL_VERIFICATION_ENABLED', 'false').lower() == 'true'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = os.environ.get('MAIL_PORT', 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')