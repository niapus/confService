import logging

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from app.core import database

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, app):
        self._app = app
        self._services = app.extensions['services']
        self._scheduler = BackgroundScheduler(
            executors={'default': ThreadPoolExecutor(max_workers=2)},
            job_defaults={
                'max_instances': 1,
                'coalesce': True,
                'misfire_grace_time': 3600,
            }
        )

    FAILED_EMAIL_RETENTION_DAYS = 30
    UNCONFIRMED_APPLICATION_RETENTION_DAYS = 7

    def start(self):
        self._scheduler.add_job(self._process_individual, 'interval', seconds=10, id='individual')
        self._scheduler.add_job(self._process_mass, 'interval', seconds=60, id='mass')
        self._scheduler.add_job(self._check_reminders, 'cron', hour=10, minute=0, id='reminders')
        self._scheduler.add_job(self._cleanup_emails, 'cron', day_of_week='sun', hour=3, minute=0, id='cleanup_emails')
        self._scheduler.add_job(self._cleanup_applications, 'cron', day_of_week='sun', hour=3, minute=30, id='cleanup_applications')
        self._scheduler.start()
        logger.info("Планировщик запущен: individual(15s), mass(60s), reminders(10:00), cleanup(вс 3:00/3:30)")

    def _process_individual(self):
        with self._app.app_context():
            sent, failed = self._services.email.process_individual_queue()
            if sent or failed:
                logger.info(f"Индивидуальная рассылка: отправлено={sent}, ошибок={failed}")

    def _process_mass(self):
        with self._app.app_context():
            sent, failed = self._services.email.process_mass_queue()
            if sent or failed:
                logger.info(f"Массовая рассылка: отправлено={sent}, ошибок={failed}")

    def _check_reminders(self):
        with self._app.app_context():
            self._do_check_reminders()

    def _do_check_reminders(self):
        session = database.Session()
        try:
            upcoming = self._services.conference.get_starting_in_days(session, days=1)
            for conference in upcoming:
                applications = self._services.application.get_application_from_schedule(conference.id, session)
                if applications:
                    self._services.notification.send_conference_reminder(applications, conference, session)
                    logger.info(f"Участников: {len(applications)}, конференция '{conference.title}'")
            session.commit()
        except Exception:
            session.rollback()
            logger.error(f"Оповещения не отправлены", exc_info=True)
        finally:
            session.close()

    def _cleanup_applications(self):
        with self._app.app_context():
            session = database.Session()
            try:
                deleted = self._services.application.cleanup_unconfirmed_older_than(self.UNCONFIRMED_APPLICATION_RETENTION_DAYS, session)
                session.commit()
                if deleted:
                    logger.info(f"Удалено неподтверждённых заявок: {deleted}")
            except Exception:
                session.rollback()
                logger.error("Ошибка при очистке неподтверждённых заявок", exc_info=True)
            finally:
                session.close()

    def _cleanup_emails(self):
        with self._app.app_context():
            session = database.Session()
            try:
                deleted = self._services.email_queue.cleanup_failed(self.FAILED_EMAIL_RETENTION_DAYS, session)
                session.commit()
                if deleted:
                    logger.info(f"Удалено FAILED писем: {deleted}")
            except Exception:
                session.rollback()
                logger.error("Ошибка при очистке очереди писем", exc_info=True)
            finally:
                session.close()