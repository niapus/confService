from unittest.mock import MagicMock

import pytest

from app.models.schedule_item import ScheduleItem, ScheduleItemType
from app.service.schedule_service import ScheduleService
from tests.factories import make_conference, make_schedule_dto


@pytest.fixture
def schedule_service(mock_conference_service, mock_thesis_service, mock_schedule_mapper,
                     mock_schedule_repository, mock_notification_service):
    return ScheduleService(
        conf_service=mock_conference_service,
        thesis_service=mock_thesis_service,
        schedule_mapper=mock_schedule_mapper,
        schedule_repository=mock_schedule_repository,
        notification=mock_notification_service
    )


class TestGetFullScheduleData:

    def test_returns_full_schedule_dto(self, schedule_service, mock_conference_service,
                                        mock_thesis_service, mock_schedule_mapper,
                                        mock_schedule_repository, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_thesis_service.get_accepted_theses_with_applications.return_value = ["ta1"]
        mock_schedule_repository.get_by_conference_id.return_value = ["s1"]
        expected_dto = MagicMock()
        mock_schedule_mapper.to_full_schedule_dto.return_value = expected_dto

        result = schedule_service.get_full_schedule_data(1, mock_session)

        mock_schedule_mapper.to_full_schedule_dto.assert_called_once_with(conf, ["ta1"], ["s1"])
        assert result == expected_dto


class TestGetSchedule:

    def test_returns_schedule(self, schedule_service, mock_schedule_repository, mock_session):
        mock_schedule_repository.get_by_conference_id.return_value = ["item1"]

        result = schedule_service.get_schedule(1, mock_session)
        assert result == ["item1"]


class TestUpdateSchedule:

    def test_update_schedule_sends_published_when_no_deleted(self, schedule_service, mock_conference_service,
                                                              mock_schedule_repository,
                                                              mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_schedule_repository.delete_all_by_conference_id.return_value = 0
        mock_notification_service.mail_enabled = True

        dto = make_schedule_dto()
        schedule_service.update_schedule(dto, 1, mock_session)

        mock_schedule_repository.delete_all_by_conference_id.assert_called_once_with(1, mock_session)
        mock_schedule_repository.create_all.assert_called_once()
        mock_notification_service.send_schedule_published.assert_called_once()

    def test_update_schedule_sends_updated_when_deleted_exist(self, schedule_service, mock_conference_service,
                                                                mock_schedule_repository,
                                                                mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_schedule_repository.delete_all_by_conference_id.return_value = 5
        mock_notification_service.mail_enabled = True

        dto = make_schedule_dto()
        schedule_service.update_schedule(dto, 1, mock_session)

        mock_notification_service.send_schedule_updated.assert_called_once()

    def test_update_schedule_no_notification_when_mail_disabled(self, schedule_service, mock_conference_service,
                                                                 mock_schedule_repository,
                                                                 mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_schedule_repository.delete_all_by_conference_id.return_value = 5
        mock_notification_service.mail_enabled = False

        dto = make_schedule_dto()
        schedule_service.update_schedule(dto, 1, mock_session)

        mock_notification_service.send_schedule_updated.assert_not_called()
        mock_notification_service.send_schedule_published.assert_not_called()

    def test_update_schedule_creates_items(self, schedule_service, mock_conference_service,
                                            mock_schedule_repository, mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_schedule_repository.delete_all_by_conference_id.return_value = 0
        mock_notification_service.mail_enabled = False

        dto = make_schedule_dto()
        schedule_service.update_schedule(dto, 1, mock_session)

        items = mock_schedule_repository.create_all.call_args[0][0]
        assert len(items) == 2
        assert items[0].item_type == ScheduleItemType.DAY
        assert items[1].item_type == ScheduleItemType.TALK

    def test_update_schedule_empty_schedule(self, schedule_service, mock_conference_service,
                                             mock_schedule_repository, mock_notification_service, mock_session):
        conf = make_conference()
        mock_conference_service.get_conference_by_id.return_value = conf
        mock_schedule_repository.delete_all_by_conference_id.return_value = 0
        mock_notification_service.mail_enabled = False

        from app.dto.dto import ScheduleDTO
        dto = ScheduleDTO(schedule=[])
        schedule_service.update_schedule(dto, 1, mock_session)

        mock_schedule_repository.create_all.assert_called_once_with([], mock_session)


class TestFillScheduleItem:

    def test_fill_schedule_item(self, schedule_service):
        from app.dto.dto import ScheduleItemDTO
        from app.models.schedule_item import ScheduleItemType

        item_dto = ScheduleItemDTO(
            item_type=ScheduleItemType.TALK,
            global_order=2,
            application_id=1,
            talk_speaker="Ivanov I.I.",
            talk_title="Test Talk",
            talk_duration=15,
            start_time="09:00",
            end_time="09:15",
        )

        result = schedule_service._fill_schedule_item(item_dto, 1)

        assert isinstance(result, ScheduleItem)
        assert result.conference_id == 1
        assert result.item_type == ScheduleItemType.TALK
        assert result.global_order == 2
        assert result.application_id == 1
        assert result.talk_speaker == "Ivanov I.I."
        assert result.talk_title == "Test Talk"
        assert result.talk_duration == 15
        assert result.start_time == "09:00"
        assert result.end_time == "09:15"
