import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "theses")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024