import os
from unittest.mock import ANY

from app.exceptions.not_found_exception import ConferenceNotFoundException, FileNotFoundException
from app.dto.dto import FullScheduleDTO, ConferenceScheduleDTO, FullApplicationDTO, ThesisInApplicationDTO
from tests.factories import make_conference, make_application


class TestApiAuthGuard:

    def test_log_files_without_session_returns_403(self, client, mock_services):
        resp = client.get("/api/log-files")
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["status_code"] == 403

    def test_logs_without_session_returns_403(self, client, mock_services):
        resp = client.get("/api/logs")
        assert resp.status_code == 403

    def test_download_log_without_session_returns_403(self, client, mock_services):
        resp = client.get("/api/download-log?file=app.log")
        assert resp.status_code == 403

    def test_conferences_without_session_returns_403(self, client, mock_services):
        resp = client.get("/api/conferences/1")
        assert resp.status_code == 403

    def test_schedule_data_without_session_returns_403(self, client, mock_services):
        resp = client.get("/api/conferences/1/schedule-data")
        assert resp.status_code == 403

    def test_update_schedule_without_session_returns_403(self, client, mock_services):
        resp = client.post("/api/schedule", json={"schedule": []})
        assert resp.status_code == 403


class TestGetLogFiles:

    def test_returns_json_list(self, admin_session, mock_services):
        mock_services["log"].get_log_files.return_value = [
            {"name": "app.log", "size": 1024}
        ]
        resp = admin_session.get("/api/log-files")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert data[0]["name"] == "app.log"
        mock_services["log"].get_log_files.assert_called_once()

    def test_empty_list(self, admin_session, mock_services):
        mock_services["log"].get_log_files.return_value = []
        resp = admin_session.get("/api/log-files")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []


class TestGetLogs:

    def test_default_params(self, admin_session, mock_services):
        mock_services["log"].read_logs.return_value = ["line1", "line2"]
        resp = admin_session.get("/api/logs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["lines"] == ["line1", "line2"]
        assert data["offset"] == 0
        assert data["limit"] == 100
        mock_services["log"].read_logs.assert_called_once_with("app.log", limit=100, offset=0)

    def test_custom_params(self, admin_session, mock_services):
        mock_services["log"].read_logs.return_value = ["line10"]
        resp = admin_session.get("/api/logs?file=error.log&offset=10&limit=50")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["offset"] == 10
        assert data["limit"] == 50
        mock_services["log"].read_logs.assert_called_once_with("error.log", limit=50, offset=10)

    def test_app_exception_returns_json_error(self, admin_session, mock_services):
        mock_services["log"].read_logs.side_effect = FileNotFoundException("missing.log")
        resp = admin_session.get("/api/logs?file=missing.log")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data
        assert data["status_code"] == 404


class TestDownloadLog:

    def test_sends_file(self, admin_session, mock_services, app):
        logs_dir = app.config["LOGS_FOLDER"]
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, "test_download.log")
        with open(log_path, "w") as f:
            f.write("test log line")

        mock_services["log"].get_file_path.return_value = log_path
        resp = admin_session.get("/api/download-log?file=test_download.log")
        assert resp.status_code == 200

        try:
            os.remove(log_path)
        except PermissionError:
            pass

    def test_file_not_found(self, admin_session, mock_services):
        mock_services["log"].get_file_path.side_effect = FileNotFoundException("missing.log")
        resp = admin_session.get("/api/download-log?file=missing.log")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "error" in data


class TestGetFullApplications:

    def test_returns_json(self, admin_session, mock_services):
        full_app = FullApplicationDTO(
            id=1, surname="Ivanov", name="Ivan", patronymic="I.",
            gender="male", birth_date=make_application().birth_date,
            degree="none", is_worker=False, is_student=True,
            work_name=None, work_place=None, work_position=None,
            study_name="Uni", study_place="City", study_level="master",
            participation_format="offline", email="ivan@test.com",
            theses=[ThesisInApplicationDTO(id=1, authors="Ivanov", title="T", file_name="t.pdf", status="pending")]
        )
        mock_services["application"].get_full_applications_for_conference.return_value = [full_app]

        resp = admin_session.get("/api/conferences/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["conference_id"] == 1
        assert len(data["applications"]) == 1
        assert data["applications"][0]["id"] == 1
        mock_services["application"].get_full_applications_for_conference.assert_called_once_with(1, ANY)

    def test_empty_applications(self, admin_session, mock_services):
        mock_services["application"].get_full_applications_for_conference.return_value = []
        resp = admin_session.get("/api/conferences/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["applications"] == []

    def test_conference_not_found(self, admin_session, mock_services):
        mock_services["application"].get_full_applications_for_conference.side_effect = ConferenceNotFoundException(1)
        resp = admin_session.get("/api/conferences/1")
        assert resp.status_code == 404


class TestGetScheduleData:

    def test_returns_json(self, admin_session, mock_services):
        conf = make_conference()
        schedule_dto = FullScheduleDTO(
            conference=ConferenceScheduleDTO(
                id=1, title="Conf", start_date=conf.start_date,
                end_date=conf.end_date, performance_time=15
            ),
            applications=[],
            schedule=[]
        )
        mock_services["schedule"].get_full_schedule_data.return_value = schedule_dto

        resp = admin_session.get("/api/conferences/1/schedule-data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "conference" in data
        assert data["conference"]["id"] == 1
        mock_services["schedule"].get_full_schedule_data.assert_called_once_with(1, ANY)

    def test_not_found(self, admin_session, mock_services):
        mock_services["schedule"].get_full_schedule_data.side_effect = ConferenceNotFoundException(1)
        resp = admin_session.get("/api/conferences/1/schedule-data")
        assert resp.status_code == 404


class TestUpdateSchedule:

    def test_success_returns_200(self, admin_session, mock_services):
        mock_services["schedule"].update_schedule.return_value = None
        payload = {
            "conference_id": 1,
            "schedule": [
                {
                    "item_type": "day",
                    "global_order": 1,
                    "day_date": "2025-08-01",
                    "day_title": "Day 1",
                    "day_start_time": "09:00",
                }
            ]
        }
        resp = admin_session.post("/api/schedule", json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        mock_services["schedule"].update_schedule.assert_called_once()

    def test_invalid_schedule_format(self, admin_session, mock_services):
        payload = {"conference_id": 1, "schedule": "not-a-list"}
        resp = admin_session.post("/api/schedule", json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_missing_schedule_key(self, admin_session, mock_services):
        payload = {"conference_id": 1}
        resp = admin_session.post("/api/schedule", json=payload)
        assert resp.status_code == 400

    def test_empty_schedule_list(self, admin_session, mock_services):
        payload = {"conference_id": 1, "schedule": []}
        resp = admin_session.post("/api/schedule", json=payload)
        assert resp.status_code == 400

    def test_invalid_item_type(self, admin_session, mock_services):
        payload = {
            "conference_id": 1,
            "schedule": [
                {
                    "item_type": "invalid_type",
                    "global_order": 1,
                }
            ]
        }
        resp = admin_session.post("/api/schedule", json=payload)
        assert resp.status_code == 400


class TestApiUnexpectedErrors:

    def test_unexpected_exception_returns_500(self, admin_session, mock_services):
        mock_services["log"].get_log_files.side_effect = RuntimeError("boom")
        resp = admin_session.get("/api/log-files")
        assert resp.status_code == 500
        data = resp.get_json()
        assert data["status_code"] == 500
