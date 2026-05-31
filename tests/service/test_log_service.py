import os
import tempfile

import pytest

from app.exceptions.file_exception import FileNullNameException
from app.exceptions.not_found_exception import FileNotFoundException
from app.service.log_service import LogService


@pytest.fixture
def logs_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def log_service(logs_folder):
    return LogService(logs_folder=logs_folder)


def create_log_file(folder, filename="app.log", content="2024-01-15 10:30:00 INFO Test log\n"):
    filepath = os.path.join(folder, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath


class TestGetLogFiles:

    def test_returns_empty_when_no_files(self, log_service, logs_folder):
        result = log_service.get_log_files()
        assert result == []

    def test_returns_app_log(self, log_service, logs_folder):
        create_log_file(logs_folder)
        result = log_service.get_log_files()
        assert len(result) == 1
        assert result[0]['name'] == 'app.log'

    def test_returns_rotated_files(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log")
        create_log_file(logs_folder, "app.log.1")
        create_log_file(logs_folder, "app.log.2")

        result = log_service.get_log_files()
        assert len(result) == 3
        assert result[0]['name'] == 'app.log'
        assert result[1]['name'] == 'app.log.1'
        assert result[2]['name'] == 'app.log.2'

    def test_stops_at_missing_rotated(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log")
        create_log_file(logs_folder, "app.log.1")

        create_log_file(logs_folder, "app.log.3")

        result = log_service.get_log_files()
        assert len(result) == 2

    def test_file_info_contains_size(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log", "x" * 1024 * 1024)  # 1MB
        result = log_service.get_log_files()
        assert result[0]['size_mb'] > 0

    def test_file_info_contains_modified_at(self, log_service, logs_folder):
        create_log_file(logs_folder)
        result = log_service.get_log_files()
        assert result[0]['modified_at'] is not None

    def test_file_info_contains_first_log_date(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log", "2024-01-15 10:30:00 INFO Test\n")
        result = log_service.get_log_files()
        assert result[0]['first_log_at'] is not None


class TestGetFirstLogDate:

    def test_parses_date_from_log(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log", "2024-03-20 14:30:00 INFO Test\n")
        result = log_service._get_first_log_date(os.path.join(logs_folder, "app.log"))
        assert result is not None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 20

    def test_returns_creation_date_when_no_date_in_log(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log", "no date here\n")
        result = log_service._get_first_log_date(os.path.join(logs_folder, "app.log"))
        assert result is not None

    def test_returns_creation_date_on_error(self, log_service, logs_folder):
        filepath = os.path.join(logs_folder, "nonexistent.log")
        with pytest.raises(FileNotFoundError):
            log_service._get_first_log_date(filepath)


class TestReadLogs:

    def test_read_logs(self, log_service, logs_folder):
        lines = [f"Line {i}\n" for i in range(20)]
        create_log_file(logs_folder, "app.log", "".join(lines))

        result = log_service.read_logs("app.log", limit=5, offset=0)
        assert len(result) <= 5

    def test_read_logs_with_offset(self, log_service, logs_folder):
        lines = [f"Line {i}\n" for i in range(20)]
        create_log_file(logs_folder, "app.log", "".join(lines))

        result = log_service.read_logs("app.log", limit=5, offset=5)
        assert len(result) <= 5

    def test_read_logs_offset_exceeds_lines(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log", "Only one line\n")

        result = log_service.read_logs("app.log", limit=10, offset=100)
        assert result == []


class TestGetFilePath:

    def test_returns_full_path(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log")

        result = log_service.get_file_path("app.log")
        assert result == os.path.join(logs_folder, "app.log")

    def test_raises_on_empty_filename(self, log_service):
        with pytest.raises(FileNullNameException):
            log_service.get_file_path("")

    def test_raises_on_nonexistent_file(self, log_service, logs_folder):
        with pytest.raises(FileNotFoundException):
            log_service.get_file_path("nonexistent.log")

    def test_uses_basename_only(self, log_service, logs_folder):
        create_log_file(logs_folder, "app.log")

        result = log_service.get_file_path("../../etc/app.log")
        assert result == os.path.join(logs_folder, "app.log")
