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
from authentik.lib.sync.api import SyncSerializer
from authentik.rbac.filters import ObjectFilter
from authentik.sources.kerberos.models import KerberosSource, KerberosSourceSync
from authentik.sources.kerberos.tasks import CACHE_KEY_STATUS


class KerberosSourceSyncSerializer(SyncSerializer):
    class Meta:
        model = KerberosSourceSync
        fields = SyncSerializer.Meta.fields + [
            "source",
            "users_count",
        ]


class KerberosSourceSerializer(SourceSerializer):
    """Kerberos Source Serializer"""

    connectivity = SerializerMethodField()
    last_sync = KerberosSourceSyncSerializer(read_only=True)

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
            "sync_outgoing_trigger_mode",
            "last_sync",
        ]
        extra_kwargs = {
            "sync_password": {"write_only": True},
            "sync_keytab": {"write_only": True},
            "spnego_keytab": {"write_only": True},
        }


class KerberosSourceViewSet(UsedByMixin, ModelViewSet):
    """Kerberos Source Viewset"""

    queryset = KerberosSource.objects.prefetch_related("kerberossourcesync_set").all()
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

    @extend_schema(responses={200: KerberosSourceSyncSerializer(many=True)})
    @action(
        methods=["GET"],
        detail=True,
        filter_backends=[ObjectFilter],
    )
    def syncs(self, request: Request, slug: str) -> Response:
        """Get provider's sync statuses"""
        source: KerberosSource = self.get_object()

        syncs = source.kerberossourcesync_set.order_by("-started_at")

        page = self.paginate_queryset(syncs)
        if page is not None:
            serializer = KerberosSourceSyncSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(KerberosSourceSyncSerializer(syncs, many=True).data)
