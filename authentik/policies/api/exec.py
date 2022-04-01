"""Serializer for policy execution"""
from rest_framework.fields import BooleanField, CharField, DictField, JSONField, ListField
from rest_framework.relations import PrimaryKeyRelatedField

from authentik.core.api.utils import PassiveSerializer, is_dict
from authentik.core.models import User


class PolicyTestSerializer(PassiveSerializer):
    """Test policy execution for a user with context"""

    user = PrimaryKeyRelatedField(queryset=User.objects.all())
    context = JSONField(required=False, validators=[is_dict])


class PolicyTestResultSerializer(PassiveSerializer):
    """result of a policy test"""

    passing = BooleanField()
    messages = ListField(child=CharField(), read_only=True)
    log_messages = ListField(child=DictField(), read_only=True)
