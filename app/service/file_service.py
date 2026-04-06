import os
import uuid

from flask import current_app

from app.utils.transliterate import safe_filename_with_cyrillic


class FileService:
    def save_thesis_file(self, file, conf_id):
        secured_filename = safe_filename_with_cyrillic(file.filename)
        ext = secured_filename.rsplit('.', 1)[1].lower()

        new_filename = f"{uuid.uuid4()}.{ext}"

        upload_dir = os.path.join(current_app.config.get("UPLOAD_FOLDER"), str(conf_id))
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, new_filename)

        file.save(file_path)

        return file_path, secured_filename

    def delete_thesis_files(self, theses):
        if not theses:
            return

        for thesis in theses:
            if os.path.exists(thesis.file_path):
                os.remove(thesis.file_path)

        folder_path = os.path.dirname(theses[0].file_path)
        if os.path.exists(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)