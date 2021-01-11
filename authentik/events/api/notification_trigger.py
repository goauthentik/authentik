"""NotificationTrigger API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.events.models import NotificationTrigger


class NotificationTriggerSerializer(ModelSerializer):
    """NotificationTrigger Serializer"""

    class Meta:

        model = NotificationTrigger
        fields = [
            "pk",
            "name",
            "transports",
            "severity",
        ]


class NotificationTriggerViewSet(ModelViewSet):
    """NotificationTrigger Viewset"""

    queryset = NotificationTrigger.objects.all()
    serializer_class = NotificationTriggerSerializer
