"""EventAlertTrigger API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet

from authentik.events.models import EventAlertTrigger


class EventAlertTriggerSerializer(ModelSerializer):
    """EventAlertTrigger Serializer"""

    class Meta:

        model = EventAlertTrigger
        fields = [
            "pk",
            "name",
            "action",
        ]


class EventAlertTriggerViewSet(ViewSet):
    """EventAlertTrigger Viewset"""

    queryset = EventAlertTrigger.objects.all()
    serializer_class = EventAlertTriggerSerializer
