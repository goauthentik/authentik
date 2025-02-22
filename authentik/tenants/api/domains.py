"""Serializer for tenants models"""

from django.apps import apps
from django.http import HttpResponseNotFound
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.tenants.api.tenants import TenantApiKeyPermission
from authentik.tenants.models import Domain


class DomainSerializer(ModelSerializer):
    """Domain Serializer"""

    class Meta:
        model = Domain
        fields = "__all__"


class DomainViewSet(ModelViewSet):
    """Domain ViewSet"""

    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    search_fields = [
        "domain",
        "tenant__name",
        "tenant__schema_name",
    ]
    ordering = ["domain"]
    authentication_classes = []
    permission_classes = [TenantApiKeyPermission]
    filter_backends = [OrderingFilter, SearchFilter]
    filterset_fields = []

    def dispatch(self, request, *args, **kwargs):
        # This only checks the license in the default tenant, which is what we want
        if not apps.get_app_config("authentik_enterprise").enabled():
            return HttpResponseNotFound()
        return super().dispatch(request, *args, **kwargs)
