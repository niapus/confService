from datetime import date

from app.mapper.application_mapper import ApplicationMapper
from app.models.thesis import ThesisStatus
from tests.factories import make_application, make_thesis


class TestApplicationMapper:

    def _make_application_with_theses(self, **app_overrides):
        app_obj = make_application(**app_overrides)
        thesis1 = make_thesis(thesis_id=1, application_id=app_obj.id, status=ThesisStatus.ACCEPTED)
        thesis2 = make_thesis(thesis_id=2, application_id=app_obj.id, title="Another Thesis",
                              authors="Petrov P.P.", status=ThesisStatus.PENDING)
        app_obj.theses = [thesis1, thesis2]
        return app_obj

    def setup_method(self):
        self.mapper = ApplicationMapper()

    def test_single_application_to_dto(self):
        app_obj = self._make_application_with_theses()
        result = self.mapper.applications_to_full_applications_dto([app_obj])

        assert len(result) == 1
        dto = result[0]

        assert dto.id == app_obj.id
        assert dto.surname == "Ivanov"
        assert dto.name == "Ivan"
        assert dto.patronymic == "Ivanovich"
        assert dto.gender == "male"
        assert dto.birth_date == date(2000, 1, 1)
        assert dto.degree == "none"
        assert dto.is_worker is False
        assert dto.is_student is True
        assert dto.participation_format == "offline"
        assert dto.email == "ivan@test.com"

    def test_theses_mapped(self):
        app_obj = self._make_application_with_theses()
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]

        assert len(dto.theses) == 2
        assert dto.theses[0].id == 1
        assert dto.theses[0].authors == "Ivanov I.I."
        assert dto.theses[0].title == "Test Thesis"
        assert dto.theses[0].file_name == "test.pdf"
        assert dto.theses[0].status == "accepted"
        assert dto.theses[1].id == 2
        assert dto.theses[1].status == "pending"

    def test_multiple_applications(self):
        app1 = self._make_application_with_theses(app_id=1)
        app2 = self._make_application_with_theses(app_id=2, surname="Petrov", email="petr@test.com")
        result = self.mapper.applications_to_full_applications_dto([app1, app2])

        assert len(result) == 2
        assert result[0].surname == "Ivanov"
        assert result[1].surname == "Petrov"

    def test_empty_list(self):
        result = self.mapper.applications_to_full_applications_dto([])
        assert result == []

    def test_no_theses(self):
        app_obj = make_application()
        app_obj.theses = []
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.theses == []

    def test_worker_fields_mapped(self):
        app_obj = self._make_application_with_theses(
            is_worker=True, is_student=False,
            work_name="Corp", work_place="City", work_position="Eng"
        )
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.work_name == "Corp"
        assert dto.work_place == "City"
        assert dto.work_position == "Eng"

    def test_student_fields_mapped(self):
        app_obj = self._make_application_with_theses(
            is_worker=False, is_student=True,
            study_name="Uni", study_place="Town"
        )
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.study_name == "Uni"
        assert dto.study_place == "Town"
        assert dto.study_level == "education_mag"

    def test_no_patronymic(self):
        app_obj = make_application(patronymic=None)
        app_obj.theses = []
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.patronymic is None

    def test_no_study_level(self):
        app_obj = make_application(is_worker=True, is_student=False)
        app_obj.study_level = None
        app_obj.theses = []
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.study_level is None

    def test_full_name_property(self):
        app_obj = make_application(surname="Ivanov", name="Ivan", patronymic="Ivanovich")
        app_obj.theses = []
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.full_name == "Ivanov Ivan Ivanovich"

    def test_full_name_without_patronymic(self):
        app_obj = make_application(surname="Ivanov", name="Ivan", patronymic=None)
        app_obj.theses = []
        dto = self.mapper.applications_to_full_applications_dto([app_obj])[0]
        assert dto.full_name == "Ivanov Ivan"
