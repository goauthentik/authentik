"""Serializer for policy execution"""
from rest_framework.fields import BooleanField, CharField, DictField, ListField
from rest_framework.relations import PrimaryKeyRelatedField

from authentik.core.api.utils import JSONDictField, PassiveSerializer
from authentik.core.models import User


class PolicyTestSerializer(PassiveSerializer):
    """Test policy execution for a user with context"""

    user = PrimaryKeyRelatedField(queryset=User.objects.all())
    context = JSONDictField(required=False)


class PolicyTestResultSerializer(PassiveSerializer):
    """result of a policy test"""

    passing = BooleanField()
    messages = ListField(child=CharField(), read_only=True)
    log_messages = ListField(child=DictField(), read_only=True)
