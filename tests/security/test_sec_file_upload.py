"""
Безопасность загрузки файлов.

FileService применяет три уровня валидации:
  1. Расширение в списке allowed_extensions;
  2. Размер ≤ max_size (в байтах);
  3. Сигнатура (magic bytes) через filetype.guess — должна совпадать с
     заявленным расширением.

Дополнительно:
  - Имя файла транслитерируется и пропускается через werkzeug.secure_filename →
    защищает от path-traversal (`../../etc/passwd`);
  - Сохранённое имя — UUID + расширение, исходное имя клиента не используется в
    пути на диске.
"""
import os
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app.exceptions.file_exception import (
    FileExtensionException, FileSignatureException, FileSizeException,
    FileNullNameException,
)
from app.service.file_service import FileService
from app.utils.transliterate import safe_filename_with_cyrillic


PDF_MAGIC = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024
ELF_MAGIC = b"\x7fELF" + b"\x00" * 1024
HTML_PAYLOAD = b"<html><script>alert(1)</script></html>" + b"\x00" * 1024


def _file(payload: bytes, filename: str) -> FileStorage:
    return FileStorage(stream=BytesIO(payload), filename=filename)


@pytest.fixture
def file_service(tmp_path):
    return FileService(
        upload_folder=str(tmp_path),
        thesis_allowed_extensions={"pdf", "docx", "doc"},
        thesis_max_size=16 * 1024 * 1024,
        proceedings_allowed_extensions={"pdf", "docx", "doc"},
        proceedings_max_size=50 * 1024 * 1024,
        conference_file_allowed_extensions={"pdf", "docx", "doc", "ppt", "pptx",
                                            "jpg", "jpeg", "png", "zip"},
        conference_file_max_size=50 * 1024 * 1024,
    )


class TestExtensionValidation:

    def test_disallowed_extension_for_thesis_rejected(self, file_service):
        # .exe не в allowed_extensions тезисов
        with pytest.raises(FileExtensionException):
            file_service.save_thesis_file(_file(PDF_MAGIC, "evil.exe"), conf_id=1)

    def test_no_extension_rejected(self, file_service):
        with pytest.raises(FileExtensionException):
            file_service.save_thesis_file(_file(PDF_MAGIC, "noext"), conf_id=1)

    def test_empty_filename_rejected(self, file_service):
        with pytest.raises(FileNullNameException):
            file_service.save_thesis_file(_file(PDF_MAGIC, ""), conf_id=1)

    def test_uppercase_extension_normalised(self, file_service):
        """PDF в верхнем регистре допустим — extension lowercased."""
        path, _ = file_service.save_thesis_file(_file(PDF_MAGIC, "doc.PDF"), conf_id=1)
        assert path.endswith(".pdf")


class TestSignatureValidation:
    """Главная защита — сигнатура должна соответствовать расширению."""

    def test_html_payload_with_pdf_extension_rejected(self, file_service):
        with pytest.raises(FileSignatureException):
            file_service.save_thesis_file(_file(HTML_PAYLOAD, "evil.pdf"), conf_id=1)

    def test_elf_with_pdf_extension_rejected(self, file_service):
        with pytest.raises(FileSignatureException):
            file_service.save_thesis_file(_file(ELF_MAGIC, "evil.pdf"), conf_id=1)

    def test_png_with_pdf_extension_rejected(self, file_service):
        with pytest.raises(FileSignatureException):
            file_service.save_thesis_file(_file(PNG_MAGIC, "image.pdf"), conf_id=1)

    def test_genuine_pdf_accepted(self, file_service, tmp_path):
        path, name = file_service.save_thesis_file(
            _file(PDF_MAGIC, "ok.pdf"), conf_id=1,
        )
        assert os.path.exists(os.path.join(str(tmp_path), path))

    def test_unknown_signature_rejected(self, file_service):
        with pytest.raises(FileSignatureException):
            file_service.save_thesis_file(
                _file(b"\x00\x01\x02\x03" + b"\x00" * 1024, "x.pdf"), conf_id=1,
            )


class TestSizeValidation:

    def test_oversize_thesis_rejected(self, file_service):
        oversize = PDF_MAGIC + b"\x00" * (16 * 1024 * 1024 + 1)
        with pytest.raises(FileSizeException):
            file_service.save_thesis_file(_file(oversize, "big.pdf"), conf_id=1)


class TestFilenameTraversal:
    """secure_filename должна вычистить '..', '/', '\\', и спецсимволы."""

    @pytest.mark.parametrize("dangerous,safe_must_not_contain", [
        ("../../etc/passwd.pdf",     ".."),
        ("..\\..\\windows\\sys.pdf", ".."),
        ("/etc/shadow.pdf",          "/etc"),
        ("\\\\server\\share.pdf",    "\\"),
        ("file\x00.pdf",             "\x00"),
        ("../../app.pdf",            "..".__add__("/")),
    ])
    def test_dangerous_path_components_stripped(self, dangerous, safe_must_not_contain):
        safe = safe_filename_with_cyrillic(dangerous)
        assert safe_must_not_contain not in safe
        # никаких слешей в финальном имени
        assert "/" not in safe and "\\" not in safe

    def test_cyrillic_filename_transliterated(self):
        safe = safe_filename_with_cyrillic("Тезис_Иванов.pdf")
        # secure_filename вычищает кириллицу полностью, поэтому транслитерация обязательна
        assert "Tezis" in safe
        assert safe.endswith(".pdf")

    def test_saved_file_uses_uuid_not_original_name(self, file_service, tmp_path):
        path, _ = file_service.save_thesis_file(
            _file(PDF_MAGIC, "secret_filename.pdf"), conf_id=42,
        )
        # путь содержит conf_id и UUID — оригинального имени там быть не должно
        assert "secret_filename" not in path
        assert "42" in path
        assert path.endswith(".pdf")


class TestSubfolderIsolation:
    """Файлы тезисов и proceedings должны лежать в разных подкаталогах."""

    def test_thesis_goes_to_theses_subfolder(self, file_service):
        path, _ = file_service.save_thesis_file(_file(PDF_MAGIC, "x.pdf"), conf_id=10)
        assert "theses" in path.replace("\\", "/").split("/")

    def test_proceedings_goes_to_proceedings_subfolder(self, file_service):
        from app.models.conference_file import ConferenceFileType
        path, _ = file_service.save_conference_file(
            _file(PDF_MAGIC, "x.pdf"), conf_id=10,
            file_type=ConferenceFileType.PROCEEDINGS,
        )
        assert "proceedings" in path.replace("\\", "/").split("/")

    def test_conference_file_goes_to_files_subfolder(self, file_service):
        from app.models.conference_file import ConferenceFileType
        path, _ = file_service.save_conference_file(
            _file(PDF_MAGIC, "x.pdf"), conf_id=10,
            file_type=ConferenceFileType.CONFERENCE_FILE,
        )
        assert "files" in path.replace("\\", "/").split("/")
