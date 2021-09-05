"""NotificationTransport API Views"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, ListField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.events.models import (
    Notification,
    NotificationSeverity,
    NotificationTransport,
    NotificationTransportError,
    TransportMode,
)


class NotificationTransportSerializer(ModelSerializer):
    """NotificationTransport Serializer"""

    mode_verbose = SerializerMethodField()

    def get_mode_verbose(self, instance: NotificationTransport) -> str:
        """Return selected mode with a UI Label"""
        return TransportMode(instance.mode).label

    class Meta:

        model = NotificationTransport
        fields = [
            "pk",
            "name",
            "mode",
            "mode_verbose",
            "webhook_url",
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
    # pylint: disable=invalid-name, unused-argument
    def test(self, request: Request, pk=None) -> Response:
        """Send example notification using selected transport. Requires
        Modify permissions."""
        transport: NotificationTransport = self.get_object()
        notification = Notification(
            severity=NotificationSeverity.NOTICE,
            body=f"Test Notification from transport {transport.name}",
            user=request.user,
        )
        try:
            response = NotificationTransportTestSerializer(
                data={"messages": transport.send(notification)}
            )
            response.is_valid()
            return Response(response.data)
        except NotificationTransportError as exc:
            return Response(str(exc.__cause__ or None), status=500)
