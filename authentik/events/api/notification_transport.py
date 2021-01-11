"""NotificationTransport API Views"""
from django.http.response import Http404
from guardian.shortcuts import get_objects_for_user
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.events.models import (
    Notification,
    NotificationSeverity,
    NotificationTransport,
)


class NotificationTransportSerializer(ModelSerializer):
    """NotificationTransport Serializer"""

    class Meta:

        model = NotificationTransport
        fields = [
            "pk",
            "name",
            "mode",
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
        transport = transports.first()
        notification = Notification(
            severity=NotificationSeverity.NOTICE,
            body=f"Test Notification from transport {transport.name}",
            user=request.user,
        )
        return Response(transport.send(notification))
