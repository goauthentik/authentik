"""Serializer for policy execution"""
from django.db.models import Model
from rest_framework.fields import BooleanField, CharField, JSONField, ListField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import Serializer

from authentik.core.models import User


class PolicyTestSerializer(Serializer):
    """Test policy execution for a user with context"""

    user = PrimaryKeyRelatedField(queryset=User.objects.all())
    context = JSONField(required=False)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class PolicyTestResultSerializer(Serializer):
    """result of a policy test"""

    passing = BooleanField()
    messages = ListField(child=CharField(), read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError
