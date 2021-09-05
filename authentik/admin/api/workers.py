"""authentik administration overview"""
from drf_spectacular.utils import extend_schema, inline_serializer
from prometheus_client import Gauge
from rest_framework.fields import IntegerField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.root.celery import CELERY_APP

GAUGE_WORKERS = Gauge("authentik_admin_workers", "Currently connected workers")


class WorkerView(APIView):
    """Get currently connected worker count."""

    permission_classes = [IsAdminUser]

    @extend_schema(responses=inline_serializer("Workers", fields={"count": IntegerField()}))
    def get(self, request: Request) -> Response:
        """Get currently connected worker count."""
        count = len(CELERY_APP.control.ping(timeout=0.5))
        return Response({"count": count})
