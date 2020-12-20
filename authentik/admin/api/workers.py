"""authentik administration overview"""
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from authentik.root.celery import CELERY_APP


class WorkerViewSet(ListModelMixin, GenericViewSet):
    """Get currently connected worker count."""

    serializer_class = Serializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):  # pragma: no cover
        return None

    def list(self, request: Request) -> Response:
        """Get currently connected worker count."""
        return Response(
            {"pagination": {"count": len(CELERY_APP.control.ping(timeout=0.5))}}
        )
