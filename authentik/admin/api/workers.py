"""authentik administration overview"""

from socket import gethostname

from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from packaging.version import parse
from rest_framework.fields import BooleanField, CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik import get_full_version
from authentik.rbac.permissions import HasPermission
from authentik.root.celery import CELERY_APP


class WorkerView(APIView):
    """Get currently connected worker count."""

    permission_classes = [HasPermission("authentik_rbac.view_system_info")]

    @extend_schema(
        responses=inline_serializer(
            "Worker",
            fields={
                "worker_id": CharField(),
                "version": CharField(),
                "version_matching": BooleanField(),
            },
            many=True,
        )
    )
    def get(self, request: Request) -> Response:
        """Get currently connected worker count."""
        raw: list[dict[str, dict]] = CELERY_APP.control.ping(timeout=0.5)
        our_version = parse(get_full_version())
        response = []
        for worker in raw:
            key = list(worker.keys())[0]
            version = worker[key].get("version")
            version_matching = False
            if version:
                version_matching = parse(version) == our_version
            response.append(
                {"worker_id": key, "version": version, "version_matching": version_matching}
            )
        # In debug we run with `task_always_eager`, so tasks are ran on the main process
        if settings.DEBUG:  # pragma: no cover
            response.append(
                {
                    "worker_id": f"authentik-debug@{gethostname()}",
                    "version": get_full_version(),
                    "version_matching": True,
                }
            )
        return Response(response)
