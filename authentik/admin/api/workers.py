"""authentik administration overview"""
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.fields import IntegerField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.root.celery import CELERY_APP


class WorkerView(APIView):
    """Get currently connected worker count."""

    permission_classes = [IsAdminUser]

    @extend_schema(responses=inline_serializer("Workers", fields={"count": IntegerField()}))
    def get(self, request: Request) -> Response:
        """Get currently connected worker count."""
        count = len(CELERY_APP.control.ping(timeout=0.5))
        # In debug we run with `task_always_eager`, so tasks are ran on the main process
        if settings.DEBUG:  # pragma: no cover
            count += 1
        return Response({"count": count})
