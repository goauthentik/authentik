"""Generic models"""

from django.db import models
from model_utils.managers import InheritanceManager
from rest_framework.serializers import BaseSerializer


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
