"""Source API Views"""

from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.lib.sync.api import SyncStatusSerializer
from authentik.rbac.filters import ObjectFilter
from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.tasks import CACHE_KEY_STATUS, kerberos_sync
from authentik.tasks.models import Task, TaskStatus


class KerberosSourceSerializer(SourceSerializer):
    """Kerberos Source Serializer"""

    connectivity = SerializerMethodField()

    def get_connectivity(self, source: KerberosSource) -> dict[str, str] | None:
        """Get cached source connectivity"""
        return cache.get(CACHE_KEY_STATUS + source.slug, None)

    class Meta:
        model = KerberosSource
        fields = SourceSerializer.Meta.fields + [
            "group_matching_mode",
            "realm",
            "krb5_conf",
            "kadmin_type",
            "sync_users",
            "sync_users_password",
            "sync_principal",
            "sync_password",
            "sync_keytab",
            "sync_ccache",
            "connectivity",
            "spnego_server_name",
            "spnego_keytab",
            "spnego_ccache",
            "password_login_update_internal_password",
        ]
        extra_kwargs = {
            "sync_password": {"write_only": True},
            "sync_keytab": {"write_only": True},
            "spnego_keytab": {"write_only": True},
        }


class KerberosSourceViewSet(UsedByMixin, ModelViewSet):
    """Kerberos Source Viewset"""

    queryset = KerberosSource.objects.all()
    serializer_class = KerberosSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "pbm_uuid",
        "name",
        "slug",
        "enabled",
        "realm",
        "kadmin_type",
        "sync_users",
        "sync_users_password",
        "sync_principal",
        "spnego_server_name",
        "password_login_update_internal_password",
    ]
    search_fields = [
        "name",
        "slug",
        "realm",
        "krb5_conf",
        "sync_principal",
        "spnego_server_name",
    ]
    ordering = ["name"]

    @extend_schema(responses={200: SyncStatusSerializer()})
    @action(
        methods=["GET"],
        detail=True,
        pagination_class=None,
        url_path="sync/status",
        filter_backends=[ObjectFilter],
    )
    def sync_status(self, request: Request, slug: str) -> Response:
        """Get provider's sync status"""
        source: KerberosSource = self.get_object()

        status = {}

        with source.sync_lock as lock_acquired:
            # If we could not acquire the lock, it means a task is using it, and thus is running
            status["is_running"] = not lock_acquired

        sync_schedule = None
        for schedule in source.schedules.all():
            if schedule.actor_name == kerberos_sync.actor_name:
                sync_schedule = schedule

        if not sync_schedule:
            return Response(SyncStatusSerializer(status).data)

        last_task: Task = (
            sync_schedule.tasks.exclude(
                aggregated_status__in=(TaskStatus.CONSUMED, TaskStatus.QUEUED)
            )
            .order_by("-mtime")
            .first()
        )
        last_successful_task: Task = (
            sync_schedule.tasks.filter(aggregated_status__in=(TaskStatus.DONE, TaskStatus.INFO))
            .order_by("-mtime")
            .first()
        )

        if last_task:
            status["last_sync_status"] = last_task.aggregated_status
        if last_successful_task:
            status["last_successful_sync"] = last_successful_task.mtime

        return Response(SyncStatusSerializer(status).data)
