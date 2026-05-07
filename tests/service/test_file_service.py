import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.exceptions.file_exception import (
    FileNullNameException, FileExtensionException,
    FileSizeException, FileSignatureException
)
from app.models.conference_file import ConferenceFileType
from app.service.file_service import FileService


@pytest.fixture
def upload_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_service(upload_folder):
    return FileService(
        upload_folder=upload_folder,
        thesis_allowed_extensions={"pdf", "docx", "doc"},
        thesis_max_size=16 * 1024 * 1024,
        proceedings_allowed_extensions={"pdf", "docx", "doc"},
        proceedings_max_size=50 * 1024 * 1024,
        conference_file_allowed_extensions={"pdf", "docx", "doc", "ppt", "pptx", "jpg", "jpeg", "png", "zip"},
        conference_file_max_size=50 * 1024 * 1024,
    )


def make_mock_file(filename="test.pdf", content=b"%PDF-1.4 test content", size=None):
    f = MagicMock()
    f.filename = filename
    if size is not None:
        f.seek = MagicMock(return_value=None)
        f.tell = MagicMock(return_value=size)
    else:
        f.seek = MagicMock(return_value=None)
        f.tell = MagicMock(return_value=len(content))
    f.read = MagicMock(return_value=content)
    f.save = MagicMock()
    return f


class TestSaveThesisFile:

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='test.pdf')
    @patch('app.service.file_service.filetype')
    def test_save_thesis_file_success(self, mock_filetype, mock_safe_name, file_service, upload_folder):
        mock_filetype.guess.return_value = MagicMock(extension='pdf')
        f = make_mock_file()

        file_path, secured = file_service.save_thesis_file(f, 1)

        assert secured == "test.pdf"
        f.save.assert_called_once()

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='test.pdf')
    @patch('app.service.file_service.filetype')
    def test_save_thesis_file_creates_directory(self, mock_filetype, mock_safe_name, file_service, upload_folder):
        mock_filetype.guess.return_value = MagicMock(extension='pdf')
        f = make_mock_file()

        file_path, secured = file_service.save_thesis_file(f, 1)

        expected_dir = os.path.join(upload_folder, "1", "theses")
        assert os.path.exists(expected_dir)


class TestSaveConferenceFile:

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='proceedings.pdf')
    @patch('app.service.file_service.filetype')
    def test_save_proceedings_file(self, mock_filetype, mock_safe_name, file_service, upload_folder):
        mock_filetype.guess.return_value = MagicMock(extension='pdf')
        f = make_mock_file(filename="proceedings.pdf")

        file_path, secured = file_service.save_conference_file(f, 1, ConferenceFileType.PROCEEDINGS)

        parts = file_path.replace('\\', '/').split('/')
        assert parts[1] == "proceedings"
        f.save.assert_called_once()

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='file.pdf')
    @patch('app.service.file_service.filetype')
    def test_save_conference_file_type(self, mock_filetype, mock_safe_name, file_service, upload_folder):
        mock_filetype.guess.return_value = MagicMock(extension='pdf')
        f = make_mock_file(filename="file.pdf")

        file_path, secured = file_service.save_conference_file(f, 1, ConferenceFileType.CONFERENCE_FILE)

        assert "files" in file_path
        f.save.assert_called_once()


class TestDeleteFiles:

    def test_delete_files_removes_existing(self, file_service, upload_folder):
        conf_dir = os.path.join(upload_folder, "1", "theses")
        os.makedirs(conf_dir, exist_ok=True)
        file_path = os.path.join(conf_dir, "test.pdf")
        with open(file_path, 'w') as f:
            f.write("test")

        mock_file = MagicMock()
        mock_file.file_path = os.path.join("1", "theses", "test.pdf")

        file_service.delete_files([mock_file])
        assert not os.path.exists(file_path)

    def test_delete_files_removes_empty_folder(self, file_service, upload_folder):
        conf_dir = os.path.join(upload_folder, "1", "theses")
        os.makedirs(conf_dir, exist_ok=True)
        file_path = os.path.join(conf_dir, "test.pdf")
        with open(file_path, 'w') as f:
            f.write("test")

        mock_file = MagicMock()
        mock_file.file_path = os.path.join("1", "theses", "test.pdf")

        file_service.delete_files([mock_file])
        assert not os.path.exists(conf_dir)

    def test_delete_files_skips_nonexistent(self, file_service, upload_folder):
        mock_file = MagicMock()
        mock_file.file_path = os.path.join("1", "theses", "nonexistent.pdf")

        file_service.delete_files([mock_file])

    def test_delete_files_empty_list(self, file_service):
        file_service.delete_files([])
        file_service.delete_files([])

    def test_delete_files_keeps_nonempty_folder(self, file_service, upload_folder):
        conf_dir = os.path.join(upload_folder, "1", "theses")
        os.makedirs(conf_dir, exist_ok=True)
        file_path = os.path.join(conf_dir, "test.pdf")
        other_path = os.path.join(conf_dir, "other.pdf")
        with open(file_path, 'w') as f:
            f.write("test")
        with open(other_path, 'w') as f:
            f.write("other")

        mock_file = MagicMock()
        mock_file.file_path = os.path.join("1", "theses", "test.pdf")

        file_service.delete_files([mock_file])
        assert not os.path.exists(file_path)
        assert os.path.exists(other_path)
        assert os.path.exists(conf_dir)


class TestValidateFilename:

    def test_empty_filename(self, file_service):
        f = make_mock_file(filename="")

        with pytest.raises(FileNullNameException):
            file_service.save_thesis_file(f, 1)

    def test_invalid_extension(self, file_service):
        f = make_mock_file(filename="test.exe")

        with pytest.raises(FileExtensionException):
            file_service.save_thesis_file(f, 1)


class TestValidateFileSize:

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='test.pdf')
    def test_file_too_large(self, mock_safe_name, file_service):
        f = make_mock_file(filename="test.pdf", size=20 * 1024 * 1024)

        with pytest.raises(FileSizeException):
            file_service.save_thesis_file(f, 1)


class TestValidateFileSignature:

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='test.pdf')
    @patch('app.service.file_service.filetype')
    def test_unknown_file_type(self, mock_filetype, mock_safe_name, file_service):
        mock_filetype.guess.return_value = None
        f = make_mock_file()

        with pytest.raises(FileSignatureException):
            file_service.save_thesis_file(f, 1)

    @patch('app.service.file_service.safe_filename_with_cyrillic', return_value='test.pdf')
    @patch('app.service.file_service.filetype')
    def test_mismatched_signature(self, mock_filetype, mock_safe_name, file_service):
        mock_filetype.guess.return_value = MagicMock(extension='docx')
        f = make_mock_file(filename="test.pdf")

        with pytest.raises(FileSignatureException):
            file_service.save_thesis_file(f, 1)


class TestGetExt:

    def test_get_ext_with_dot(self, file_service):
        assert file_service._FileService__get_ext("test.pdf") == "pdf"

    def test_get_ext_without_dot(self, file_service):
        assert file_service._FileService__get_ext("test") == ""

    def test_get_ext_multiple_dots(self, file_service):
        assert file_service._FileService__get_ext("my.file.name.docx") == "docx"

    def test_get_ext_case_insensitive(self, file_service):
        assert file_service._FileService__get_ext("test.PDF") == "pdf"
