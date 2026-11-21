"""Daily reporter-data retention for AED reports through Celery (same rule as purge_aed_reporter_data)."""
from celery.schedules import crontab

from mcod.core.tasks import extended_shared_task

TASK_NAME = 'mcod.aed_reports.tasks.purge_reporter_data_task'


@extended_shared_task(name=TASK_NAME)
def purge_reporter_data_task():
    from mcod.aed_reports.services import purge_reporter_data
    return {'cleaned': purge_reporter_data()}


def register_beat_schedule():
    from mcod.celeryapp import app
    app.conf.beat_schedule.setdefault('aed-reporter-data-retention', {'task': TASK_NAME, 'schedule': crontab(minute=15, hour=4)})
