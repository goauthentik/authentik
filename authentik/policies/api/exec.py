"""Serializer for policy execution"""
from rest_framework.fields import BooleanField, CharField, JSONField, ListField
from rest_framework.relations import PrimaryKeyRelatedField

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User


class PolicyTestSerializer(PassiveSerializer):
    """Test policy execution for a user with context"""

    user = PrimaryKeyRelatedField(queryset=User.objects.all())
    context = JSONField(required=False)


class PolicyTestResultSerializer(PassiveSerializer):
    """result of a policy test"""

    passing = BooleanField()
    messages = ListField(child=CharField(), read_only=True)
