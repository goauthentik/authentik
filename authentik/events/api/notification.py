"""Notification API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.events.models import Notification


class NotificationSerializer(ModelSerializer):
    """Notification Serializer"""

    class Meta:

        model = Notification
        fields = [
            "pk",
            "severity",
            "body",
            "created",
            "event",
            "seen",
        ]


class NotificationViewSet(ModelViewSet):
    """Notification Viewset"""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        return Notification.objects.filter(user=self.request.user)
