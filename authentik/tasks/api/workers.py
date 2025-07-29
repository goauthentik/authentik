import pglock
from django.utils.timezone import now, timedelta
from drf_spectacular.utils import extend_schema, inline_serializer
from packaging.version import parse
from rest_framework.fields import BooleanField, CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik import get_full_version
from authentik.rbac.permissions import HasPermission
from authentik.tasks.models import WorkerStatus


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
        response = []
        our_version = parse(get_full_version())
        for status in WorkerStatus.objects.filter(last_seen__gt=now() - timedelta(minutes=2)):
            lock_id = f"goauthentik.io/worker/status/{status.pk}"
            with pglock.advisory(lock_id, timeout=0, side_effect=pglock.Return) as acquired:
                # The worker doesn't hold the lock, it isn't running
                if acquired:
                    continue
                version_matching = parse(status.version) == our_version
                response.append(
                    {
                        "worker_id": f"{status.pk}@{status.hostname}",
                        "version": status.version,
                        "version_matching": version_matching,
                    }
                )
        return Response(response)
