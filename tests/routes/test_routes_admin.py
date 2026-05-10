import io
import os
import tempfile
from unittest.mock import ANY, MagicMock, patch

from app.exceptions.conversion_exception import EmptyRequiredFieldException, InvalidFieldFormatException
from app.exceptions.conflict_exception import ApplicationAlreadyExists
from app.exceptions.file_exception import FileSizeException, FileExtensionException
from app.exceptions.not_found_exception import ConferenceNotFoundException, FileNotFoundException
from app.models.conference_file import ConferenceFileType
from app.models.thesis import ThesisStatus
from tests.factories import make_conference, make_application, make_thesis, make_conference_file


# ─── Auth guard (before_request) ───────────────────────────────────────────────

class TestAdminAuthGuard:

    def test_get_admin_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin")
        assert resp.status_code == 403

    def test_get_create_conference_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/conferences/create")
        assert resp.status_code == 403

    def test_post_new_conference_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/conferences/new", data={"title": "X"})
        assert resp.status_code == 403

    def test_get_conference_page_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/conferences/1")
        assert resp.status_code == 403

    def test_logout_without_session_returns_403(self, client, mock_services):
        # logout is also behind before_request
        resp = client.get("/admin/logout")
        assert resp.status_code == 403

    def test_get_logs_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/logs")
        assert resp.status_code == 403

    def test_post_edit_conference_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/conferences/1/edit", data={"title": "X"})
        assert resp.status_code == 403

    def test_post_delete_conference_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/conferences/1/delete")
        assert resp.status_code == 403

    def test_post_upload_proceedings_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/conferences/1/upload/proceedings", data={"title": "X"})
        assert resp.status_code == 403

    def test_post_upload_file_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/conferences/1/upload/file", data={"title": "X"})
        assert resp.status_code == 403

    def test_get_view_conference_file_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/conferences/files/1/view")
        assert resp.status_code == 403

    def test_post_delete_conference_file_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/conferences/1/files/1/delete")
        assert resp.status_code == 403

    def test_get_view_thesis_file_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/thesis/1/view")
        assert resp.status_code == 403

    def test_post_update_thesis_status_without_session_returns_403(self, client, mock_services):
        resp = client.post("/admin/theses/1/status", data={"status": "accepted"})
        assert resp.status_code == 403

    def test_get_thesis_page_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/applications/1/thesis/1")
        assert resp.status_code == 403

    def test_get_schedule_page_without_session_returns_403(self, client, mock_services):
        resp = client.get("/admin/conferences/1/schedule")
        assert resp.status_code == 403


# ─── GET conference endpoints ────────────────────────────────────────────────────

class TestShowAdminCreateConference:

    def test_returns_200(self, admin_session, mock_services):
        resp = admin_session.get("/admin/conferences/create")
        assert resp.status_code == 200


class TestShowUpdateConference:

    def test_returns_200(self, admin_session, mock_services):
        mock_services["conference"].get_conference_by_id.return_value = make_conference()
        resp = admin_session.get("/admin/conferences/1/edit")
        assert resp.status_code == 200
        mock_services["conference"].get_conference_by_id.assert_called_once_with(1, ANY)

    def test_not_found(self, admin_session, mock_services):
        mock_services["conference"].get_conference_by_id.side_effect = ConferenceNotFoundException(999)
        resp = admin_session.get("/admin/conferences/999/edit")
        assert resp.status_code == 404


class TestShowAdminConferences:

    def test_returns_200(self, admin_session, mock_services):
        mock_services["conference"].get_all_conferences.return_value = [make_conference()]
        mock_services["thesis"].get_all_theses.return_value = [make_thesis()]
        mock_services["application"].get_all_applications.return_value = []
        resp = admin_session.get("/admin")
        assert resp.status_code == 200

    def test_calls_all_services(self, admin_session, mock_services):
        mock_services["conference"].get_all_conferences.return_value = []
        mock_services["thesis"].get_all_theses.return_value = []
        mock_services["application"].get_all_applications.return_value = []
        admin_session.get("/admin")
        mock_services["conference"].get_all_conferences.assert_called_once()
        mock_services["thesis"].get_all_theses.assert_called_once()
        mock_services["application"].get_all_applications.assert_called_once()

    def test_empty_data(self, admin_session, mock_services):
        mock_services["conference"].get_all_conferences.return_value = []
        mock_services["thesis"].get_all_theses.return_value = []
        mock_services["application"].get_all_applications.return_value = []
        resp = admin_session.get("/admin")
        assert resp.status_code == 200


class TestConferencePage:

    def test_returns_200(self, admin_session, mock_services):
        mock_services["conference"].exists.return_value = True
        resp = admin_session.get("/admin/conferences/1")
        assert resp.status_code == 200
        mock_services["conference"].exists.assert_called_once_with(1, ANY)

    def test_not_found(self, admin_session, mock_services):
        mock_services["conference"].exists.side_effect = ConferenceNotFoundException(1)
        resp = admin_session.get("/admin/conferences/1")
        assert resp.status_code == 404


# ─── POST conference endpoints ───────────────────────────────────────────────────

class TestCreateConference:

    def test_success_redirects(self, admin_session, mock_services):
        conf = make_conference(conf_id=10, title="New Conf")
        mock_services["conference"].create_conference.return_value = conf
        resp = admin_session.post("/admin/conferences/new", data={
            "title": "New Conf",
            "description_md": "# Desc",
            "tagline": "Tag",
            "registration_deadline": "2025-06-01",
            "submission_deadline": "2025-07-01",
            "start_date": "2025-08-01",
            "end_date": "2025-08-03",
            "performance_time": "15",
        })
        assert resp.status_code == 302
        assert "/admin" in resp.headers["Location"]
        mock_services["conference"].create_conference.assert_called_once()

    def test_validation_error_renders_form(self, admin_session, mock_services):
        # Empty title -> build_conference_dto raises EmptyRequiredFieldException
        resp = admin_session.post("/admin/conferences/new", data={
            "title": "",
            "description_md": "# Desc",
            "registration_deadline": "2025-06-01",
            "submission_deadline": "2025-07-01",
            "start_date": "2025-08-01",
            "end_date": "2025-08-03",
            "performance_time": "15",
        })
        # handle_form_errors catches ConversionException -> renders template
        assert resp.status_code == 200

    def test_invalid_date_format(self, admin_session, mock_services):
        resp = admin_session.post("/admin/conferences/new", data={
            "title": "Conf",
            "description_md": "# Desc",
            "registration_deadline": "not-a-date",
            "submission_deadline": "2025-07-01",
            "start_date": "2025-08-01",
            "end_date": "2025-08-03",
            "performance_time": "15",
        })
        assert resp.status_code == 200  # re-renders form with error


class TestUpdateConference:

    def test_success_redirects(self, admin_session, mock_services):
        conf = make_conference(conf_id=5, title="Updated")
        mock_services["conference"].update_conference.return_value = conf
        resp = admin_session.post("/admin/conferences/5/edit", data={
            "title": "Updated",
            "description_md": "# Desc",
            "tagline": "Tag",
            "registration_deadline": "2025-06-01",
            "submission_deadline": "2025-07-01",
            "start_date": "2025-08-01",
            "end_date": "2025-08-03",
            "performance_time": "15",
        })
        assert resp.status_code == 302
        assert "/admin" in resp.headers["Location"]
        mock_services["conference"].update_conference.assert_called_once_with(5, ANY, ANY)

    def test_validation_error_renders_form_with_conf_id(self, admin_session, mock_services):
        resp = admin_session.post("/admin/conferences/5/edit", data={
            "title": "",
            "description_md": "# Desc",
            "registration_deadline": "2025-06-01",
            "submission_deadline": "2025-07-01",
            "start_date": "2025-08-01",
            "end_date": "2025-08-03",
            "performance_time": "15",
        })
        # handle_form_errors("conference_form.html", True) -> pass_conf_id=True
        assert resp.status_code == 200


class TestDeleteConference:

    def test_success_redirects(self, admin_session, mock_services):
        conf = make_conference(conf_id=3, title="To Delete")
        mock_services["conference"].get_conference_by_id.return_value = conf
        resp = admin_session.post("/admin/conferences/3/delete")
        assert resp.status_code == 302
        assert "/admin" in resp.headers["Location"]
        mock_services["thesis"].delete_all_conference_theses_files.assert_called_once_with(3, ANY)
        mock_services["conference_file"].delete_all_conference_files.assert_called_once_with(3, ANY)
        mock_services["conference"].delete_conference.assert_called_once_with(conf, ANY)

    def test_not_found(self, admin_session, mock_services):
        mock_services["conference"].get_conference_by_id.side_effect = ConferenceNotFoundException(999)
        resp = admin_session.post("/admin/conferences/999/delete")
        assert resp.status_code == 404


# ─── File endpoints ──────────────────────────────────────────────────────────────

class TestUploadProceedings:

    def test_success_redirects(self, admin_session, mock_services):
        mock_services["conference_file"].create_conference_file.return_value = None
        data = {"title": "Proceedings 2024"}
        data["file"] = (io.BytesIO(b"%PDF-1.4 fake"), "test.pdf")
        resp = admin_session.post("/admin/conferences/1/upload/proceedings",
                                  data=data, content_type="multipart/form-data")
        assert resp.status_code == 302
        assert "/admin/conferences/1/edit" in resp.headers["Location"]
        mock_services["conference_file"].create_conference_file.assert_called_once()
        call_args = mock_services["conference_file"].create_conference_file.call_args
        assert call_args[0][3] == ConferenceFileType.PROCEEDINGS

    def test_file_error(self, admin_session, mock_services):
        mock_services["conference_file"].create_conference_file.side_effect = FileSizeException(50)
        data = {"title": "Big file"}
        data["file"] = (io.BytesIO(b"x" * 100), "huge.pdf")
        resp = admin_session.post("/admin/conferences/1/upload/proceedings",
                                  data=data, content_type="multipart/form-data")
        # FileException is caught by global AppException handler (not handle_form_errors)
        assert resp.status_code == 400


class TestUploadFile:

    def test_success_redirects(self, admin_session, mock_services):
        mock_services["conference_file"].create_conference_file.return_value = None
        data = {"title": "Presentation"}
        data["file"] = (io.BytesIO(b"%PDF-1.4 fake"), "pres.pptx")
        resp = admin_session.post("/admin/conferences/1/upload/file",
                                  data=data, content_type="multipart/form-data")
        assert resp.status_code == 302
        assert "/admin/conferences/1/edit" in resp.headers["Location"]
        call_args = mock_services["conference_file"].create_conference_file.call_args
        assert call_args[0][3] == ConferenceFileType.CONFERENCE_FILE


class TestViewConferenceFile:

    def test_sends_file(self, admin_session, mock_services, app):
        conf_file = make_conference_file(file_id=1, file_path="1/proceedings/test.pdf", original_name="test.pdf")
        mock_services["conference_file"].get_file_by_id.return_value = conf_file

        # Create the actual file so send_from_directory works
        upload_dir = app.config["UPLOAD_FOLDER"]
        file_dir = os.path.join(upload_dir, "1", "proceedings")
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, "test.pdf")
        with open(file_path, "w") as f:
            f.write("fake pdf content")

        resp = admin_session.get("/admin/conferences/files/1/view")
        assert resp.status_code == 200

        # Cleanup (ignore Windows file-in-use errors)
        try:
            os.remove(file_path)
        except PermissionError:
            pass

    def test_file_not_found_in_db(self, admin_session, mock_services):
        mock_services["conference_file"].get_file_by_id.side_effect = ConferenceNotFoundException(999)
        resp = admin_session.get("/admin/conferences/files/999/view")
        assert resp.status_code == 404


class TestDeleteConferenceFile:

    def test_success_redirects(self, admin_session, mock_services):
        mock_services["conference_file"].delete_conference_file.return_value = None
        resp = admin_session.post("/admin/conferences/1/files/5/delete")
        assert resp.status_code == 302
        assert "/admin/conferences/1/edit" in resp.headers["Location"]
        mock_services["conference_file"].delete_conference_file.assert_called_once_with(5, ANY)


class TestViewThesisFile:

    def test_sends_file(self, admin_session, mock_services, app):
        thesis = make_thesis(thesis_id=1, file_path="1/theses/test.pdf", file_name="test.pdf")
        mock_services["thesis"].get_thesis_by_id.return_value = thesis

        upload_dir = app.config["UPLOAD_FOLDER"]
        file_dir = os.path.join(upload_dir, "1", "theses")
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, "test.pdf")
        with open(file_path, "w") as f:
            f.write("fake thesis content")

        resp = admin_session.get("/admin/thesis/1/view")
        assert resp.status_code == 200

        try:
            os.remove(file_path)
        except PermissionError:
            pass

    def test_thesis_not_found(self, admin_session, mock_services):
        from app.exceptions.not_found_exception import ThesisNotFoundException
        mock_services["thesis"].get_thesis_by_id.side_effect = ThesisNotFoundException(999)
        resp = admin_session.get("/admin/thesis/999/view")
        assert resp.status_code == 404


# ─── Thesis status ───────────────────────────────────────────────────────────────

class TestUpdateThesisStatus:

    def test_success_redirects(self, admin_session, mock_services):
        thesis = make_thesis(thesis_id=1, title="My Thesis")
        thesis.status = ThesisStatus.ACCEPTED
        mock_services["thesis"].update_thesis_status.return_value = thesis

        resp = admin_session.post("/admin/theses/1/status", data={"status": "accepted"})
        assert resp.status_code == 302
        assert "/admin" in resp.headers["Location"]
        mock_services["thesis"].update_thesis_status.assert_called_once_with(1, "accepted", ANY)
        mock_services["notification"].send_thesis_status.assert_called_once_with(thesis, ANY)

    def test_success_with_mail_enabled(self, admin_session, mock_services):
        thesis = make_thesis(thesis_id=2, title="Thesis Mail")
        thesis.status = ThesisStatus.REJECTED
        mock_services["thesis"].update_thesis_status.return_value = thesis
        mock_services["notification"].mail_enabled = True
        mock_services["notification"].send_thesis_status.return_value = None

        resp = admin_session.post("/admin/theses/2/status", data={"status": "rejected"})
        assert resp.status_code == 302
        mock_services["notification"].send_thesis_status.assert_called_once_with(thesis, ANY)


class TestViewThesisPage:

    def test_returns_200(self, admin_session, mock_services):
        thesis = make_thesis()
        thesis.application = make_application()
        thesis.application.conference = make_conference()
        mock_services["thesis"].get_thesis_by_id.return_value = thesis
        resp = admin_session.get("/admin/applications/1/thesis/1")
        assert resp.status_code == 200
        mock_services["thesis"].get_thesis_by_id.assert_called_once_with(1, ANY)


# ─── Logout ──────────────────────────────────────────────────────────────────────

class TestLogout:

    def test_redirects_to_root(self, admin_session, mock_services):
        resp = admin_session.get("/admin/logout")
        assert resp.status_code == 302
        assert "/" in resp.headers["Location"]

    def test_clears_session(self, admin_session, mock_services):
        admin_session.get("/admin/logout")
        with admin_session.session_transaction() as sess:
            assert "admin_id" not in sess
            assert "admin_login" not in sess


# ─── Schedule page ───────────────────────────────────────────────────────────────

class TestViewSchedulePage:

    def test_returns_200(self, admin_session, mock_services):
        mock_services["conference"].exists.return_value = True
        resp = admin_session.get("/admin/conferences/1/schedule")
        assert resp.status_code == 200
        mock_services["conference"].exists.assert_called_once_with(1, ANY)

    def test_not_found(self, admin_session, mock_services):
        mock_services["conference"].exists.side_effect = ConferenceNotFoundException(1)
        resp = admin_session.get("/admin/conferences/1/schedule")
        assert resp.status_code == 404


# ─── Logs page ───────────────────────────────────────────────────────────────────

class TestViewLogs:

    def test_returns_200(self, admin_session, mock_services):
        resp = admin_session.get("/admin/logs")
        assert resp.status_code == 200
