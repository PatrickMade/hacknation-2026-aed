from django.apps import AppConfig


class AedReportsConfig(AppConfig):
    name = 'mcod.aed_reports'
    verbose_name = 'Zgłoszenia AED'

    def ready(self):
        from mcod.aed_reports.tasks import register_beat_schedule
        register_beat_schedule()
