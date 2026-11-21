"""Periodic refresh of the AED report through Celery (same code path as the aed_refresh command)."""
from celery.schedules import crontab

from mcod.core.tasks import extended_shared_task

TASK_NAME = 'mcod.aed_aggregate.tasks.aed_refresh_task'


@extended_shared_task(name=TASK_NAME)
def aed_refresh_task():
    from mcod.aed_aggregate.refresh import refresh
    result = refresh()
    result.pop('rejected', None)
    return result


def register_beat_schedule():
    from mcod.celeryapp import app
    app.conf.beat_schedule.setdefault('aed-refresh-daily', {'task': TASK_NAME, 'schedule': crontab(minute=30, hour=3)})
