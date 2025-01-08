"""Notification API Views"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
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
    owner_field = "user"

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Marked tasks as read successfully."),
        },
    )
    @action(detail=False, methods=["post"])
    def mark_all_seen(self, request: Request) -> Response:
        """Mark all the user's notifications as seen"""
        Notification.objects.filter(user=request.user, seen=False).update(seen=True)
        return Response({}, status=204)
