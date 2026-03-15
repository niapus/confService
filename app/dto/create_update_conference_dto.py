from datetime import date, datetime


class CreateUpdateConferenceDTO:

    def __init__(self, form_data):
        self.title = form_data.get('title')
        self.registration_deadline = form_data.get('registration_deadline')
        self.submission_deadline = form_data.get('submission_deadline')
        self.program_date = form_data.get('program_date')
        self.start_date = form_data.get('start_date')
        self.end_date = form_data.get('end_date')
        self.description_md = form_data.get('description_md')
        self.tagline = form_data.get('tagline')
        self.performance_time = form_data.get('performance_time')