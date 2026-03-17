from typing import Optional

from app.dto.dto import FullApplicationDTO, ThesisInApplicationDTO
from app.models.application import Application
from app.models.thesis import Thesis


class ApplicationMapper:
    def __to_dto(self, application: Application, thesis: Optional[Thesis]) -> FullApplicationDTO:
        thesis_dto = None

        if thesis:
            thesis_dto = ThesisInApplicationDTO(
                id=thesis.id,
                title=thesis.title,
                file_path=thesis.file_path,
                file_name=thesis.file_name,
                status=thesis.status.value
            )

        return FullApplicationDTO(
            id=application.id,
            surname=application.surname,
            name=application.name,
            patronymic=application.patronymic,
            gender=application.gender.value,
            birth_date=application.birth_date,
            degree=application.degree.value,
            is_worker=application.is_worker,
            is_student=application.is_student,
            work_name=application.work_name,
            work_place=application.work_place,
            work_position=application.work_position,
            study_name=application.study_name,
            study_place=application.study_place,
            study_level=application.study_level.value,
            participation_format=application.participation_format.value,
            email=application.email,
            thesis_info=thesis_dto
        )

    def from_query_result_to_full_application_dto(self, query_result):
        result = []

        for app, thesis in query_result:
            dto = self.__to_dto(app, thesis)
            result.append(dto)

        return result