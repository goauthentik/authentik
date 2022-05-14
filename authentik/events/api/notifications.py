"""Notification API Views"""
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.events.api.events import EventSerializer
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
    UsedByMixin,
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
        "user",
    ]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Marked tasks as read successfully."),
        },
    )
    @action(detail=False, methods=["post"])
    def mark_all_seen(self, request: Request) -> Response:
        """Mark all the user's notifications as seen"""
        notifications = Notification.objects.filter(user=request.user)
        for notification in notifications:
            notification.seen = True
        Notification.objects.bulk_update(notifications, ["seen"])
        return Response({}, status=204)
