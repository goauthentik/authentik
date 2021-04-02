"""Serializer mixin for managed models"""
from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer


class ManagedSerializer(PassiveSerializer):
    """Managed Serializer"""

    managed = CharField(read_only=True, allow_null=True)
