import os
import re
from datetime import datetime, timezone

from app.exceptions.file_exception import FileNullNameException
from app.exceptions.not_found_exception import FileNotFoundException


class LogService:
    """Чтение и навигация по лог-файлам приложения."""

    def __init__(self, logs_folder: str) -> None:
        self.logs_folder = logs_folder

    def get_log_files(self) -> list[dict]:
        """Возвращает список лог-файлов (основной + ротированные) с метаданными."""
        files = []
        base_file = os.path.join(self.logs_folder, 'app.log')

        if os.path.exists(base_file):
            files.append(self._get_file_info(base_file))

        for i in range(1, 6):
            rotated_file = f"{base_file}.{i}"
            if os.path.exists(rotated_file):
                files.append(self._get_file_info(rotated_file))
            else:
                break

        return files

    def _get_file_info(self, file_path: str) -> dict:
        """Собирает метаданные лог-файла: имя, размер, время изменения и дату первой записи."""
        stat = os.stat(file_path)
        first_log_date = self._get_first_log_date(file_path)
        return {
            'name': os.path.basename(file_path),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            'first_log_at': first_log_date if first_log_date else None
        }

    def _get_first_log_date(self, file_path: str) -> datetime | None:
        """Читает первые 10 строк файла и возвращает дату первой записи."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if match:
                        naive_dt = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                        return naive_dt.astimezone(timezone.utc)
            return datetime.fromtimestamp(os.stat(file_path).st_ctime, tz=timezone.utc)
        except Exception:
            return datetime.fromtimestamp(os.stat(file_path).st_ctime, tz=timezone.utc)

    def read_logs(self, filename: str, limit: int = 100, offset: int = 0) -> list[str]:
        """Читает строки лог-файла с конца.

        Args:
            filename: Имя файла (без пути) в папке логов.
            limit: Количество строк для возврата.
            offset: Смещение от конца файла (0 — последние строки, 100 — строки перед ними).
        """
        filepath = self.get_file_path(filename)

        with open(filepath, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()

            block_size = 1024
            data = b''
            lines_found = 0
            target_lines = offset + limit

            while file_size > 0 and target_lines > lines_found:
                step = min(block_size, file_size)
                file_size -= step
                f.seek(file_size)
                chunk = f.read(step)
                data = chunk + data
                lines_found = data.count(b'\n')

            lines = data.split(b'\n')

            if offset >= len(lines):
                return []

            start = max(0, len(lines) - offset - limit)
            end = len(lines) - offset
            return [line.decode('utf-8', errors='ignore') for line in lines[start:end]]

    def get_file_path(self, filename: str) -> str:
        """Возвращает абсолютный путь к лог-файлу. Выбрасывает исключение если файл не существует."""
        if not filename:
            raise FileNullNameException()
        filename = os.path.basename(filename)
        file_path = os.path.join(self.logs_folder, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundException(filename)
        return file_path
