from django.db import models


class AedPublication(models.Model):
    """Record of a resource published by the wizard after passing aed-standard/validate.py.

    Plain ids instead of foreign keys keep this app's migration free of dependencies:
    upstream migrations rely on an implicit order that an extra dependency chain would change.
    Portal objects are only soft-deleted, so the ids stay resolvable.
    """

    organization_id = models.PositiveIntegerField(db_index=True)
    dataset_id = models.PositiveIntegerField()
    resource_id = models.PositiveIntegerField()
    created_by_id = models.PositiveIntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    records_count = models.PositiveIntegerField()
    warnings_count = models.PositiveIntegerField(default=0)
    standard_version = models.CharField(max_length=20)
    source_name = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("-created", "-id")
        verbose_name = "Publikacja zgodna ze standardem AED"
        verbose_name_plural = "Publikacje zgodne ze standardem AED"

    @property
    def organization(self):
        from mcod.organizations.models import Organization

        return Organization.raw.get(pk=self.organization_id)

    @property
    def dataset(self):
        from mcod.datasets.models import Dataset

        return Dataset.raw.get(pk=self.dataset_id)

    @property
    def resource(self):
        from mcod.resources.models import Resource

        return Resource.raw.get(pk=self.resource_id)
