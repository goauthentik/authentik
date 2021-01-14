"""Notification API Views"""
from rest_framework import mixins
from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.events.models import Notification


class NotificationSerializer(ModelSerializer):
    """Notification Serializer"""

    body = ReadOnlyField()
    severity = ReadOnlyField()
    created = ReadOnlyField()
    event = ReadOnlyField()

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


class NotificationViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Notification Viewset"""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        return Notification.objects.filter(user=self.request.user)
