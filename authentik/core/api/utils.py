"""API Utilities"""
from typing import Any

from django.db.models import Model
from rest_framework.fields import CharField, IntegerField, JSONField
from rest_framework.serializers import Serializer, SerializerMethodField, ValidationError


def is_dict(value: Any):
    """Ensure a value is a dictionary, useful for JSONFields"""
    if isinstance(value, dict):
        return
    raise ValidationError("Value must be a dictionary, and not have any duplicate keys.")


class PassiveSerializer(Serializer):
    """Base serializer class which doesn't implement create/update methods"""

    def create(self, validated_data: dict) -> Model:  # pragma: no cover
        return Model()

    def update(self, instance: Model, validated_data: dict) -> Model:  # pragma: no cover
        return Model()


class PropertyMappingPreviewSerializer(PassiveSerializer):
    """Preview how the current user is mapped via the property mappings selected in a provider"""

    preview = JSONField(read_only=True)


class MetaNameSerializer(PassiveSerializer):
    """Add verbose names to response"""

    verbose_name = SerializerMethodField()
    verbose_name_plural = SerializerMethodField()
    meta_model_name = SerializerMethodField()

    def get_verbose_name(self, obj: Model) -> str:
        """Return object's verbose_name"""
        return obj._meta.verbose_name

    def get_verbose_name_plural(self, obj: Model) -> str:
        """Return object's plural verbose_name"""
        return obj._meta.verbose_name_plural

    def get_meta_model_name(self, obj: Model) -> str:
        """Return internal model name"""
        return f"{obj._meta.app_label}.{obj._meta.model_name}"


class TypeCreateSerializer(PassiveSerializer):
    """Types of an object that can be created"""

    name = CharField(required=True)
    description = CharField(required=True)
    component = CharField(required=True)
    model_name = CharField(required=True)


class CacheSerializer(PassiveSerializer):
    """Generic cache stats for an object"""

    count = IntegerField(read_only=True)


class LinkSerializer(PassiveSerializer):
    """Returns a single link"""

    link = CharField()
