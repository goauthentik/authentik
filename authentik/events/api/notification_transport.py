"""NotificationTransport API Views"""
from django.http.response import Http404
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

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

    def get_mode_verbose(self, instance: NotificationTransport):
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
        ]


class NotificationTransportViewSet(ModelViewSet):
    """NotificationTransport Viewset"""

    queryset = NotificationTransport.objects.all()
    serializer_class = NotificationTransportSerializer

    @action(detail=True, methods=["post"])
    # pylint: disable=invalid-name
    def test(self, request: Request, pk=None) -> Response:
        """Send example notification using selected transport. Requires
        Modify permissions."""
        transports = get_objects_for_user(
            request.user, "authentik_events.change_notificationtransport"
        ).filter(pk=pk)
        if not transports.exists():
            raise Http404
        transport: NotificationTransport = transports.first()
        notification = Notification(
            severity=NotificationSeverity.NOTICE,
            body=f"Test Notification from transport {transport.name}",
            user=request.user,
        )
        try:
            return Response(transport.send(notification))
        except NotificationTransportError as exc:
            return Response(str(exc.__cause__ or None), status=503)
