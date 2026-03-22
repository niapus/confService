from app.dto.dto import FullApplicationDTO, ThesisInApplicationDTO
from app.models.application import Application
from app.models.thesis import Thesis


class ApplicationMapper:
    def __to_dto(self, application: Application) -> FullApplicationDTO:
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
            theses=[self.__thesis_to_dto(t) for t in application.theses]
        )

    def __thesis_to_dto(self, thesis: Thesis) -> ThesisInApplicationDTO:
        return ThesisInApplicationDTO(
            id=thesis.id,
            authors=thesis.authors,
            title=thesis.title,
            file_path=thesis.file_path,
            file_name=thesis.file_name,
            status=thesis.status.value
        )


    def applications_to_full_applications_dto(self, applications):
        return [self.__to_dto(app) for app in applications]