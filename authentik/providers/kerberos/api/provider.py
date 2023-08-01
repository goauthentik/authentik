"""KerberosProvider API Views"""
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
    extend_schema_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    IntegerField,
    ListField,
    ReadOnlyField,
    SerializerMethodField,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.providers.kerberos.lib.crypto import SUPPORTED_ENCTYPES
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm


class KerberosProviderRealmNamesSerializer(PassiveSerializer):
    """Realm names returned with a KerberosProvider query"""

    pk = IntegerField()
    name = CharField()
    realm_name = CharField()


class KerberosProviderSerializer(ProviderSerializer):
    """KerberosProvider Serializer"""

    url_download_keytab = SerializerMethodField()
    realm_names = SerializerMethodField()

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
            "is_tgs",
            "url_download_keytab",
            "realm_names",
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

    @extend_schema_field(KerberosProviderRealmNamesSerializer(many=True))
    def get_realm_names(self, instance: KerberosProvider) -> list[dict[str, str | int]]:
        return [
            {
                "pk": realm.pk,
                "name": realm.name,
                "realm_name": realm.realm_name,
            }
            for realm in instance.realms.all()
        ]


class EnctypeSerializer(Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


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

    @extend_schema(responses={200: EnctypeSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def enctypes(self, request):
        enctypes = []
        for enctype in SUPPORTED_ENCTYPES:
            enctypes.append({"name": enctype.ENC_NAME, "id": enctype.ENC_TYPE.value})
        serializer = EnctypeSerializer(enctypes, many=True)
        return Response(serializer.data)

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

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    url_kdc_proxy = SerializerMethodField()
    url_download_dns_records = SerializerMethodField()
    url_download_krb5_conf = SerializerMethodField()

    class Meta:
        model = KerberosRealm
        fields = KerberosProviderSerializer.Meta.fields + [
            "realm_name",
            "user_to_principal_pm",
            "principal_to_user_pm",
            "outpost_set",
            "url_kdc_proxy",
            "url_download_dns_records",
            "url_download_krb5_conf",
        ]
        extra_kwargs = {
            "authentication_flow": {"required": True, "allow_null": False},
            "spn": {"required": False, "allow_null": True},
        }

    def validate(self, data):
        if (
            data["user_to_principal_pm"] is not None
            and data["principal_to_user_pm"] is None
            or data["user_to_principal_pm"] is None
            and data["principal_to_user_pm"] is not None
        ):
            raise serializers.ValidationError(
                "Both user to principal and principal to user mappings must be set, or neither of them must be set."
            )
        return data

    def get_url_kdc_proxy(self, instance: KerberosProvider) -> str:
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        return request.build_absolute_uri(
            reverse(
                "authentik_providers_kerberos:kdc-proxy", kwargs={"realm_name": instance.realm_name}
            )
        )

    def get_url_download_dns_records(self, instance: KerberosProvider) -> str:
        """Get URL where to download the realm DNS records"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        return request.build_absolute_uri(
            reverse("authentik_api:kerberosrealm-dnsrecords", kwargs={"pk": instance.pk})
            + "?download"
        )

    def get_url_download_krb5_conf(self, instance: KerberosProvider) -> str:
        """Get URL where to download the realm krb5.conf"""
        if "request" not in self._context:
            return ""
        request: HttpRequest = self._context["request"]._request
        return request.build_absolute_uri(
            reverse("authentik_api:kerberosrealm-krb5conf", kwargs={"pk": instance.pk})
            + "?download"
        )


class KerberosRealmDnsRecordsSerializer(PassiveSerializer):
    """Kerberos realm DNS records serializer"""

    dns_records = CharField(read_only=True)


class KerberosRealmKrb5ConfSerializer(PassiveSerializer):
    """Kerberos realm krb5.conf serializer"""

    krb5_conf = CharField(read_only=True)


class KerberosRealmViewSet(KerberosProviderViewSet):
    """KerberosRealm Viewset"""

    queryset = KerberosRealm.objects.all()
    serializer_class = KerberosRealmSerializer

    @extend_schema(
        responses={
            200: KerberosRealmDnsRecordsSerializer(many=False),
        },
    )
    @action(methods=["GET"], detail=True, permission_classes=[AllowAny])
    def dnsrecords(self, request: Request, pk: int) -> Response:
        """Return dns records for a realm"""
        # We don't use self.get_object() on purpose as this view is un-authenticated
        realm: KerberosRealm = KerberosRealm.objects.filter(pk=pk).first()
        if not realm:
            return Response(status=404)
        kdc_proxy = request.build_absolute_uri(
            reverse(
                "authentik_providers_kerberos:kdc-proxy", kwargs={"realm_name": realm.realm_name}
            )
        )
        records_raw = (
            f'_kerberos.{realm.realm_name} TXT "{realm.realm_name}"',
            f"_kerberos.{realm.realm_name} URI 10 1 krb5srv::kkdcp:{kdc_proxy}",
        )
        records = "\n".join(records_raw)

        return Response({"dns_records": records})

    @extend_schema(
        responses={
            200: KerberosRealmKrb5ConfSerializer(many=False),
        },
        parameters=[
            OpenApiParameter(
                name="download", location=OpenApiParameter.QUERY, type=OpenApiTypes.BOOL
            ),
        ],
    )
    @action(methods=["GET"], detail=True, permission_classes=[AllowAny])
    def krb5conf(self, request: Request, pk: int) -> Response:
        """Return krb5.conf for a realm"""
        # We don't use self.get_object() on purpose as this view is un-authenticated
        realm: KerberosRealm = KerberosRealm.objects.filter(pk=pk).first()
        if not realm:
            return Response(status=404)
        kdc_proxy = request.build_absolute_uri(
            reverse(
                "authentik_providers_kerberos:kdc-proxy", kwargs={"realm_name": realm.realm_name}
            )
        )
        krb5_conf_raw = (
            "[libdefaults]",
            f"  default_realm = {realm.realm_name}",
            "  dns_canonicalize_hostname = false",
            "  dns_fallback = true",
            "",
            "[realms]",
            f"  {realm.realm_name} = {{",
            f"    kdc = {kdc_proxy}",
            "  }",
        )
        krb5_conf = "\n".join(krb5_conf_raw)

        if "download" in request.query_params:
            response = HttpResponse(krb5_conf, content_type="text/plain")
            response["Content-Disposition"] = f'attachment; filename="krb5.conf"'
            return response
        return Response({"krb5_conf": krb5_conf})


class KerberosOutpostConfigSerializer(KerberosRealmSerializer):
    """KerberosOutpostConfig serializer"""

    class Meta:
        model = KerberosRealm
        fields = [
            "pk",
            "name",
            "realm_name",
            "url_kdc_proxy",
        ]


class KerberosOutpostConfigViewSet(ReadOnlyModelViewSet):
    """KerberosOutpostConfig Viewset"""

    queryset = KerberosRealm.objects.all()
    serializer_class = KerberosOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]
