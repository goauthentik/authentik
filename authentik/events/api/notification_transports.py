"""NotificationTransport API Views"""
from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.events.models import (
    Event,
    Notification,
    NotificationSeverity,
    NotificationTransport,
    NotificationTransportError,
    TransportMode,
)
from authentik.events.utils import get_user


class NotificationTransportSerializer(ModelSerializer):
    """NotificationTransport Serializer"""

    mode_verbose = SerializerMethodField()

    def get_mode_verbose(self, instance: NotificationTransport) -> str:
        """Return selected mode with a UI Label"""
        return TransportMode(instance.mode).label

    def validate(self, attrs: dict[Any, str]) -> dict[Any, str]:
        """Ensure the required fields are set."""
        mode = attrs.get("mode")
        if mode in [TransportMode.WEBHOOK, TransportMode.WEBHOOK_SLACK]:
            if "webhook_url" not in attrs or attrs.get("webhook_url", "") == "":
                raise ValidationError({"webhook_url": "Webhook URL may not be empty."})
        return attrs

    class Meta:
        model = NotificationTransport
        fields = [
            "pk",
            "name",
            "mode",
            "mode_verbose",
            "webhook_url",
            "webhook_mapping",
            "send_once",
        ]


class NotificationTransportTestSerializer(PassiveSerializer):
    """Notification test serializer"""

    messages = ListField(child=CharField())


class NotificationTransportViewSet(UsedByMixin, ModelViewSet):
    """NotificationTransport Viewset"""

    queryset = NotificationTransport.objects.all()
    serializer_class = NotificationTransportSerializer
    filterset_fields = ["name", "mode", "webhook_url", "send_once"]
    search_fields = ["name", "mode", "webhook_url"]
    ordering = ["name"]

    @permission_required("authentik_events.change_notificationtransport")
    @extend_schema(
        responses={
            200: NotificationTransportTestSerializer(many=False),
            500: OpenApiResponse(description="Failed to test transport"),
        },
        request=OpenApiTypes.NONE,
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Send example notification using selected transport. Requires
        Modify permissions."""
        transport: NotificationTransport = self.get_object()
        event = Event.new(
            action="notification_test",
            user=get_user(request.user),
            app=self.__class__.__module__,
            context={"foo": "bar"},
        )
        event.save()
        notification = Notification(
            severity=NotificationSeverity.NOTICE,
            body=f"Test Notification from transport {transport.name}",
            user=request.user,
            event=event,
        )
        try:
            response = NotificationTransportTestSerializer(
                data={"messages": transport.send(notification)}
            )
            response.is_valid()
            return Response(response.data)
        except NotificationTransportError as exc:
            return Response(str(exc.__cause__ or None), status=500)
