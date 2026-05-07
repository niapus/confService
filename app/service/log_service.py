import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from app.exceptions.file_exception import FileNullNameException
from app.exceptions.not_found_exception import FileNotFoundException


class LogService:
    def __init__(self, logs_folder: str):
        self.logs_folder = logs_folder
    
    def get_log_files(self) -> List[Dict]:
        """Получить список лог-файлов с информацией"""
        files = []
        
        # Ищем app.log и ротированные файлы
        base_file = os.path.join(self.logs_folder, 'app.log')
        if os.path.exists(base_file):
            files.append(self._get_file_info(base_file))
        
        # Ищем ротированные файлы
        for i in range(1, 6):
            rotated_file = f"{base_file}.{i}"
            if os.path.exists(rotated_file):
                files.append(self._get_file_info(rotated_file))
            else:
                break
        
        return files
    
    def _get_file_info(self, file_path: str) -> Dict:
        """Получить информацию о файле"""
        stat = os.stat(file_path)
        
        # Получаем дату первого лога
        first_log_date = self._get_first_log_date(file_path)
        
        return {
            'name': os.path.basename(file_path),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            'first_log_at': first_log_date.replace(tzinfo=timezone.utc) if first_log_date else None
        }
    
    def _get_first_log_date(self, file_path: str) -> Optional[datetime]:
        """Получить дату первого лога из файла"""
        try:
            # Читаем первые несколько строк для поиска даты
            with open(file_path, 'r', encoding='utf-8') as f:
                for i in range(10):  # проверяем первые 10 строк
                    line = f.readline()
                    if not line:
                        break
                    
                    # Ищем дату в формате YYYY-MM-DD HH:MM:SS
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if date_match:
                        date_str = date_match.group(1)
                        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            
            # Если не нашли дату в логах, возвращаем время создания файла
            return datetime.fromtimestamp(os.stat(file_path).st_ctime, tz=timezone.utc)
            
        except Exception:
            # В случае ошибки возвращаем время создания файла
            return datetime.fromtimestamp(os.stat(file_path).st_ctime, tz=timezone.utc)

    def read_logs(self, filename, limit=100, offset=0):

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
            result = lines[start:end]

            return [line.decode('utf-8', errors='ignore') for line in result]
    
    def get_file_path(self, filename: str) -> str:
        """Получить полный путь к файлу"""
        if not filename:
            raise FileNullNameException()

        filename = os.path.basename(filename)
        file_path = os.path.join(self.logs_folder, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundException(filename)

        return file_path