"""NotificationRule API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.events.models import NotificationRule


class NotificationRuleSerializer(ModelSerializer):
    """NotificationRule Serializer"""

    class Meta:

        model = NotificationRule
        depth = 2
        fields = [
            "pk",
            "name",
            "transports",
            "severity",
            "group",
        ]


class NotificationRuleViewSet(ModelViewSet):
    """NotificationRule Viewset"""

    queryset = NotificationRule.objects.all()
    serializer_class = NotificationRuleSerializer
