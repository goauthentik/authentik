"""NotificationTransport API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.events.models import NotificationTransport


class NotificationTransportSerializer(ModelSerializer):
    """NotificationTransport Serializer"""

    class Meta:

        model = NotificationTransport
        fields = [
            "pk",
            "name",
        ]


class NotificationTransportViewSet(ModelViewSet):
    """NotificationTransport Viewset"""

    queryset = NotificationTransport.objects.all()
    serializer_class = NotificationTransportSerializer
