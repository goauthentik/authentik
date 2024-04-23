"""Generic models"""

from typing import Any

from django.db import models
from django.dispatch import Signal
from django.utils import timezone
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer

pre_soft_delete = Signal()
post_soft_delete = Signal()


class SerializerModel(models.Model):
    """Base Abstract Model which has a serializer"""

    class Meta:
        abstract = True

    @property
    def serializer(self) -> type[BaseSerializer]:
        """Get serializer for this model"""
        raise NotImplementedError


class CreatedUpdatedModel(models.Model):
    """Base Abstract Model to save created and update"""

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InheritanceAutoManager(InheritanceManager):
    """Object manager which automatically selects the subclass"""

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class InheritanceForwardManyToOneDescriptor(models.fields.related.ForwardManyToOneDescriptor):
    """Forward ManyToOne Descriptor that selects subclass. Requires InheritanceAutoManager."""

    def get_queryset(self, **hints):
        return self.field.remote_field.model.objects.db_manager(hints=hints).select_subclasses()


class InheritanceForeignKey(models.ForeignKey):
    """Custom ForeignKey that uses InheritanceForwardManyToOneDescriptor"""

    forward_related_accessor_class = InheritanceForwardManyToOneDescriptor


class SoftDeleteQuerySet(models.query.QuerySet):

    def delete(self):
        for obj in self.all():
            obj.delete()

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    """Model which doesn't fully delete itself, but rather saved the delete status
    so cleanup events can run."""

    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def delete(self, using: Any = ..., keep_parents: bool = ...) -> tuple[int, dict[str, int]]:
        pre_soft_delete.send(sender=self.__class__, instance=self)
        now = timezone.now()
        self.deleted_at = now
        self.save(
            update_fields=[
                "deleted_at",
            ]
        )
        post_soft_delete.send(sender=self.__class__, instance=self)
        return tuple()

    def force_delete(self, using: Any = ...):
        if not self.deleted_at:
            raise models.ProtectedError("Refusing to force delete non-deleted model", {self})
        return super().delete(using=using)
