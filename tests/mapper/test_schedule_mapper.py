from datetime import date

from app.mapper.schedule_mapper import ScheduleMapper
from app.models.schedule_item import ScheduleItem, ScheduleItemType
from tests.factories import make_conference, make_application, make_thesis


class TestScheduleMapper:

    def setup_method(self):
        self.mapper = ScheduleMapper()

    def _make_conference(self):
        conf = make_conference()
        return conf

    def _make_thesis_with_app(self, app_id=1, surname="Ivanov", name="Ivan", patronymic="Ivanovich"):
        app_obj = make_application(app_id=app_id, surname=surname, name=name, patronymic=patronymic)
        thesis = make_thesis(thesis_id=app_id, application_id=app_id)
        return thesis, app_obj

    def _make_schedule_item(self, item_type=ScheduleItemType.DAY, global_order=1):
        si = ScheduleItem()
        si.id = global_order
        si.conference_id = 1
        si.item_type = item_type
        si.global_order = global_order

        if item_type == ScheduleItemType.DAY:
            si.day_date = date(2025, 8, 1)
            si.day_title = "Day 1"
            si.day_start_time = "09:00"
        elif item_type == ScheduleItemType.TALK:
            si.application_id = 1
            si.talk_speaker = "Ivanov I.I."
            si.talk_title = "Talk 1"
            si.talk_duration = 15
            si.start_time = "09:00"
            si.end_time = "09:15"
        elif item_type == ScheduleItemType.BREAK:
            si.break_title = "Coffee"
            si.break_duration = 15
            si.start_time = "09:15"
            si.end_time = "09:30"
        elif item_type == ScheduleItemType.TEXT:
            si.text_content = "Welcome!"

        return si

    def test_to_full_schedule_dto(self):
        conf = self._make_conference()
        thesis, app_obj = self._make_thesis_with_app()
        schedule_items = [self._make_schedule_item()]

        dto = self.mapper.to_full_schedule_dto(conf, [(thesis, app_obj)], schedule_items)

        assert dto.conference.id == conf.id
        assert dto.conference.title == conf.title
        assert len(dto.applications) == 1
        assert len(dto.schedule) == 1

    def test_conference_schedule_dto(self):
        conf = self._make_conference()
        dto = self.mapper.to_full_schedule_dto(conf, [], [])

        assert dto.conference.id == conf.id
        assert dto.conference.title == "Test Conference"
        assert dto.conference.performance_time == 15

    def test_conference_dates_formatted(self):
        conf = self._make_conference()
        dto = self.mapper.to_full_schedule_dto(conf, [], [])

        assert dto.conference.start_date == conf.start_date.strftime('%Y-%m-%d')
        assert dto.conference.end_date == conf.end_date.strftime('%Y-%m-%d')

    def test_thesis_with_patronymic(self):
        conf = self._make_conference()
        thesis, app_obj = self._make_thesis_with_app(surname="Ivanov", name="Ivan", patronymic="Ivanovich")

        dto = self.mapper.to_full_schedule_dto(conf, [(thesis, app_obj)], [])

        assert dto.applications[0].speaker_name == "Ivanov Ivan Ivanovich"
        assert dto.applications[0].id == thesis.id
        assert dto.applications[0].title == thesis.title

    def test_thesis_without_patronymic(self):
        conf = self._make_conference()
        thesis, app_obj = self._make_thesis_with_app(surname="Petrov", name="Petr", patronymic=None)

        dto = self.mapper.to_full_schedule_dto(conf, [(thesis, app_obj)], [])

        assert dto.applications[0].speaker_name == "Petrov Petr"

    def test_multiple_theses(self):
        conf = self._make_conference()
        t1, a1 = self._make_thesis_with_app(app_id=1, surname="Ivanov", name="Ivan")
        t2, a2 = self._make_thesis_with_app(app_id=2, surname="Petrov", name="Petr")

        dto = self.mapper.to_full_schedule_dto(conf, [(t1, a1), (t2, a2)], [])

        assert len(dto.applications) == 2
        assert dto.applications[0].speaker_name.startswith("Ivanov")
        assert dto.applications[1].speaker_name.startswith("Petrov")

    def test_empty_theses(self):
        conf = self._make_conference()
        dto = self.mapper.to_full_schedule_dto(conf, [], [])
        assert dto.applications == []

    def test_schedule_items_to_dicts(self):
        conf = self._make_conference()
        items = [
            self._make_schedule_item(ScheduleItemType.DAY, 1),
            self._make_schedule_item(ScheduleItemType.TALK, 2),
        ]

        dto = self.mapper.to_full_schedule_dto(conf, [], items)

        assert len(dto.schedule) == 2
        assert dto.schedule[0]['item_type'] == 'day'
        assert dto.schedule[1]['item_type'] == 'talk'

    def test_empty_schedule(self):
        conf = self._make_conference()
        dto = self.mapper.to_full_schedule_dto(conf, [], [])
        assert dto.schedule == []
