"""API Utilities"""
from typing import Any

from django.db.models import Model
from rest_framework.fields import BooleanField, CharField, FileField, IntegerField
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


class FileUploadSerializer(PassiveSerializer):
    """Serializer to upload file"""

    file = FileField(required=False)
    clear = BooleanField(default=False)


class FilePathSerializer(PassiveSerializer):
    """Serializer to upload file"""

    url = CharField()


class MetaNameSerializer(PassiveSerializer):
    """Add verbose names to response"""

    verbose_name = SerializerMethodField()
    verbose_name_plural = SerializerMethodField()

    def get_verbose_name(self, obj: Model) -> str:
        """Return object's verbose_name"""
        return obj._meta.verbose_name

    def get_verbose_name_plural(self, obj: Model) -> str:
        """Return object's plural verbose_name"""
        return obj._meta.verbose_name_plural


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
