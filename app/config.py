import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "theses")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ADMIN_LOGIN = os.environ.get('ADMIN_LOGIN', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')

    SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key')