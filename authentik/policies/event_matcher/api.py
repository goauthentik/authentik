"""Event Matcher Policy API"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.policies.forms import GENERAL_SERIALIZER_FIELDS
from authentik.policies.event_matcher.models import EventMatcherPolicy


class EventMatcherPolicySerializer(ModelSerializer):
    """Event Matcher Policy Serializer"""

    class Meta:
        model = EventMatcherPolicy
        fields = GENERAL_SERIALIZER_FIELDS + [
            "action",
            "client_ip",
        ]


class EventMatcherPolicyViewSet(ModelViewSet):
    """Event Matcher Policy Viewset"""

    queryset = EventMatcherPolicy.objects.all()
    serializer_class = EventMatcherPolicySerializer
