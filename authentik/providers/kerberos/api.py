"""KerberosProvider API Views"""
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, ListField, ReadOnlyField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer
from authentik.providers.kerberos.lib.protocol import PrincipalName
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm


class KerberosProviderSerializer(ProviderSerializer):
    """KerberosProvider Serializer"""

    url_download_keytab = SerializerMethodField()

    class Meta:
        model = KerberosProvider
        fields = ProviderSerializer.Meta.fields + [
            "spn",
            "realms",
            "maximum_skew",
            "maximum_ticket_lifetime",
            "maximum_ticket_renew_lifetime",
            "allowed_enctypes",
            "allow_postdateable",
            "allow_renewable",
            "allow_proxiable",
            "allow_forwardable",
            "requires_preauth",
            "set_ok_as_delegate",
            "secret",
            "url_download_keytab",
            "is_tgs",
        ]
        extra_kwargs = {}

    def get_url_download_keytab(self, instance: KerberosProvider) -> str:
        """Get URL where to download provider's keytab"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        return request.build_absolute_uri(
            reverse("authentik_api:kerberosprovider-keytab", kwargs={"pk": instance.pk})
        )


class KerberosProviderViewSet(UsedByMixin, ModelViewSet):
    """KerberosProvider Viewset"""

    queryset = KerberosProvider.objects.filter(kerberosrealm__isnull=True)
    serializer_class = KerberosProviderSerializer
    ordering = ["name"]
    search_fields = ["name", "spn", "realms__spn"]
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
        "authorization_flow__slug": ["iexact"],
    }

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Service keytab"),
        }
    )
    @action(detail=True, methods=["GET"])
    def keytab(self, request: Request, pk: str) -> HttpResponse:
        """Retrieve the provider keytab"""
        provider: KerberosProvider = self.get_object()
        keytab = provider.kerberoskeys.keytab(provider.principal_name, provider.realms.all())
        return HttpResponse(
            keytab.to_bytes(),
            content_type="application/octet-stream",
            headers={
                "Content-Disposition": "attachment; filename=krb5.keytab",
            },
        )


class KerberosRealmSerializer(KerberosProviderSerializer):
    """KerberosRealm Serializer"""

    class Meta:
        model = KerberosRealm
        fields = KerberosProviderSerializer.Meta.fields + [
            "realm_name",
        ]
        extra_kwargs = {
            "authentication_flow": {"required": True, "allow_null": False},
        }


class KerberosRealmViewSet(KerberosProviderViewSet):
    """KerberosRealm Viewset"""

    queryset = KerberosRealm.objects.all()
    serializer_class = KerberosRealmSerializer
