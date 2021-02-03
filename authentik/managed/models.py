"""Managed Object models"""
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


class ManagedModel(models.Model):
    """Model which can be managed by authentik exclusively"""

    managed = models.BooleanField(
        default=False,
        verbose_name=_("Managed by authentik"),
        help_text=_(
            (
                "Objects which are managed by authentik. These objects are created and updated "
                "automatically. This is flag only indicates that an object can be overwritten by "
                "migrations. You can still modify the objects via the API, but expect changes "
                "to be overwritten in a later update."
            )
        ),
    )

    def managed_objects(self) -> QuerySet:
        """Get all objects which are managed"""
        return self.objects.filter(managed=True)

    class Meta:

        abstract = True
