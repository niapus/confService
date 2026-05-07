from app.exceptions.not_found_exception import FileNotFoundException
from app.exceptions.validation_exception import ValidationException
from app.models.conference_file import ConferenceFileType, ConferenceFile
from app.repository.conference_file_repository import ConferenceFileRepository
from app.service.conference_service import ConferenceService
from app.service.file_service import FileService


class ConferenceFileService:
    def __init__(self, file_service: FileService, conference_service: ConferenceService, conference_file_repository: ConferenceFileRepository):
        self.__file_service = file_service
        self.__conf_service = conference_service
        self.__repo = conference_file_repository

    def create_conference_file(self, file, dto, conf_id, file_type: ConferenceFileType, session):
        self.__conf_service.exists(conf_id, session)
        
        if file_type == ConferenceFileType.PROCEEDINGS:
            existing_proceedings = self.__repo.get_proceedings(conf_id, session)
            if existing_proceedings:
                raise ValidationException("Сборник тезисов уже загружен. Удалите существующий файл перед загрузкой нового.")

        file_path, secured_filename = self.__file_service.save_conference_file(file, conf_id, file_type)

        conf_file = ConferenceFile(
            conference_id=conf_id,
            file_type=file_type,
            original_name=secured_filename,
            file_path=file_path,
            title=dto.title
        )

        return self.__repo.save(conf_file, session)

    def get_file_by_id(self, file_id, session):
        conf_file = self.__repo.get_by_id(file_id, session)
        if not conf_file:
            raise FileNotFoundException(file_id)
        return conf_file

    def delete_conference_file(self, file_id, session):
        conf_file = self.__repo.get_by_id(file_id, session)
        self.__repo.delete(conf_file, session)
        self.__file_service.delete_files([conf_file])

    def delete_all_conference_files(self, conf_id, session):
        files = self.__repo.get_all_by_conf_id(conf_id, session)
        self.__file_service.delete_files(files)