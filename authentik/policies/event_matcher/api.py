"""Event Matcher Policy API"""
from rest_framework.viewsets import ModelViewSet

from authentik.policies.api import PolicySerializer
from authentik.policies.event_matcher.models import EventMatcherPolicy


class EventMatcherPolicySerializer(PolicySerializer):
    """Event Matcher Policy Serializer"""

    class Meta:
        model = EventMatcherPolicy
        fields = PolicySerializer.Meta.fields + [
            "action",
            "client_ip",
            "app",
        ]


class EventMatcherPolicyViewSet(ModelViewSet):
    """Event Matcher Policy Viewset"""

    queryset = EventMatcherPolicy.objects.all()
    serializer_class = EventMatcherPolicySerializer
