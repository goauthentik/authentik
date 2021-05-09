"""Notification API Views"""
from django_filters.rest_framework import DjangoFilterBackend
from guardian.utils import get_anonymous_user
from rest_framework import mixins
from rest_framework.fields import ReadOnlyField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.events.api.event import EventSerializer
from authentik.events.models import Notification


class NotificationSerializer(ModelSerializer):
    """Notification Serializer"""

    body = ReadOnlyField()
    severity = ReadOnlyField()
    event = EventSerializer(required=False)

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
    filterset_fields = [
        "severity",
        "body",
        "created",
        "event",
        "seen",
    ]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        return Notification.objects.filter(user=user.pk)
