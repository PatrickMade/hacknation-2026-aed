"""Periodic refresh of the AED report through Celery (same code path as the aed_refresh command)."""
from celery.schedules import crontab

from mcod.core.tasks import extended_shared_task

TASK_NAME = 'mcod.aed_aggregate.tasks.aed_refresh_task'


@extended_shared_task(name=TASK_NAME)
def aed_refresh_task():
    from django.conf import settings
    from mcod.aed_aggregate.refresh import refresh
    if settings.ENVIRONMENT != 'local':
        return {'skipped': 'aed_refresh_task is restricted to ENVIRONMENT=local'}
    result = refresh()
    result.pop('rejected', None)
    return result


def register_beat_schedule():
    """Daily AED refresh. With AED_BEAT_ONLY=1 (Compose service aed-beat) the beat process keeps only the AED
    tasks, so the local stack runs the daily refresh without the upstream portal's periodic jobs."""
    import os

    from mcod.celeryapp import app
    if os.environ.get('AED_BEAT_ONLY') == '1':
        for name in [name for name, entry in app.conf.beat_schedule.items()
                     if not str(entry.get('task', '')).startswith('mcod.aed_')]:
            del app.conf.beat_schedule[name]
    app.conf.beat_schedule.setdefault('aed-refresh-daily', {'task': TASK_NAME, 'schedule': crontab(minute=30, hour=3),
                                                            'options': {'queue': 'periodic'}})
