"""Serializer mixin for managed models"""
from rest_framework.fields import CharField


class ManagedSerializer:
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)
