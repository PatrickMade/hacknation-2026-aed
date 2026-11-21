from django.apps import AppConfig


class AedAggregateConfig(AppConfig):
    name = 'mcod.aed_aggregate'
    verbose_name = 'Raport zbiorczy AED'

    def ready(self):
        from mcod.aed_aggregate.tasks import register_beat_schedule
        register_beat_schedule()
