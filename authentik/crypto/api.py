"""Crypto API Views"""
from datetime import datetime
from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from django.http.response import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from django_filters.filters import BooleanFilter
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, DateTimeField, IntegerField, SerializerMethodField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.authorization import SecretKeyFilter
from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction

LOGGER = get_logger()


class CertificateKeyPairSerializer(ModelSerializer):
    """CertificateKeyPair Serializer"""

    fingerprint_sha256 = SerializerMethodField()
    fingerprint_sha1 = SerializerMethodField()

    cert_expiry = SerializerMethodField()
    cert_subject = SerializerMethodField()
    private_key_available = SerializerMethodField()
    private_key_type = SerializerMethodField()

    certificate_download_url = SerializerMethodField()
    private_key_download_url = SerializerMethodField()

    @property
    def _should_include_details(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_details", "true")).lower() == "true"

    def get_fingerprint_sha256(self, instance: CertificateKeyPair) -> Optional[str]:
        "Get certificate Hash (SHA256)"
        if not self._should_include_details:
            return None
        return instance.fingerprint_sha256

    def get_fingerprint_sha1(self, instance: CertificateKeyPair) -> Optional[str]:
        "Get certificate Hash (SHA1)"
        if not self._should_include_details:
            return None
        return instance.fingerprint_sha1

    def get_cert_expiry(self, instance: CertificateKeyPair) -> Optional[datetime]:
        "Get certificate expiry"
        if not self._should_include_details:
            return None
        return DateTimeField().to_representation(instance.certificate.not_valid_after)

    def get_cert_subject(self, instance: CertificateKeyPair) -> Optional[str]:
        """Get certificate subject as full rfc4514"""
        if not self._should_include_details:
            return None
        return instance.certificate.subject.rfc4514_string()

    def get_private_key_available(self, instance: CertificateKeyPair) -> bool:
        """Show if this keypair has a private key configured or not"""
        return instance.key_data != "" and instance.key_data is not None

    def get_private_key_type(self, instance: CertificateKeyPair) -> Optional[str]:
        """Get the private key's type, if set"""
        if not self._should_include_details:
            return None
        key = instance.private_key
        if key:
            return key.__class__.__name__.replace("_", "").lower().replace("privatekey", "")
        return None

    def get_certificate_download_url(self, instance: CertificateKeyPair) -> str:
        """Get URL to download certificate"""
        return (
            reverse(
                "authentik_api:certificatekeypair-view-certificate",
                kwargs={"pk": instance.pk},
            )
            + "?download"
        )

    def get_private_key_download_url(self, instance: CertificateKeyPair) -> str:
        """Get URL to download private key"""
        return (
            reverse(
                "authentik_api:certificatekeypair-view-private-key",
                kwargs={"pk": instance.pk},
            )
            + "?download"
        )

    def validate_certificate_data(self, value: str) -> str:
        """Verify that input is a valid PEM x509 Certificate"""
        try:
            # Cast to string to fully load and parse certificate
            # Prevents issues like https://github.com/goauthentik/authentik/issues/2082
            str(load_pem_x509_certificate(value.encode("utf-8"), default_backend()))
        except ValueError as exc:
            LOGGER.warning("Failed to load certificate", exc=exc)
            raise ValidationError("Unable to load certificate.")
        return value

    def validate_key_data(self, value: str) -> str:
        """Verify that input is a valid PEM Key"""
        # Since this field is optional, data can be empty.
        if value != "":
            try:
                # Cast to string to fully load and parse certificate
                # Prevents issues like https://github.com/goauthentik/authentik/issues/2082
                str(
                    load_pem_private_key(
                        str.encode("\n".join([x.strip() for x in value.split("\n")])),
                        password=None,
                        backend=default_backend(),
                    )
                )
            except (ValueError, TypeError) as exc:
                LOGGER.warning("Failed to load private key", exc=exc)
                raise ValidationError("Unable to load private key (possibly encrypted?).")
        return value

    class Meta:
        model = CertificateKeyPair
        fields = [
            "pk",
            "name",
            "fingerprint_sha256",
            "fingerprint_sha1",
            "certificate_data",
            "key_data",
            "cert_expiry",
            "cert_subject",
            "private_key_available",
            "private_key_type",
            "certificate_download_url",
            "private_key_download_url",
            "managed",
        ]
        extra_kwargs = {
            "managed": {"read_only": True},
            "key_data": {"write_only": True},
            "certificate_data": {"write_only": True},
        }


class CertificateDataSerializer(PassiveSerializer):
    """Get CertificateKeyPair's data"""

    data = CharField(read_only=True)


class CertificateGenerationSerializer(PassiveSerializer):
    """Certificate generation parameters"""

    common_name = CharField()
    subject_alt_name = CharField(required=False, allow_blank=True, label=_("Subject-alt name"))
    validity_days = IntegerField(initial=365)


class CertificateKeyPairFilter(FilterSet):
    """Filter for certificates"""

    has_key = BooleanFilter(
        label="Only return certificate-key pairs with keys", method="filter_has_key"
    )

    def filter_has_key(self, queryset, name, value):  # pragma: no cover
        """Only return certificate-key pairs with keys"""
        return queryset.exclude(key_data__exact="")

    class Meta:
        model = CertificateKeyPair
        fields = ["name", "managed"]


class CertificateKeyPairViewSet(UsedByMixin, ModelViewSet):
    """CertificateKeyPair Viewset"""

    queryset = CertificateKeyPair.objects.exclude(managed=MANAGED_KEY)
    serializer_class = CertificateKeyPairSerializer
    filterset_class = CertificateKeyPairFilter
    ordering = ["name"]
    search_fields = ["name"]
    filter_backends = [SecretKeyFilter, OrderingFilter, SearchFilter]

    @extend_schema(
        parameters=[
            # Override the type for `has_key` above
            OpenApiParameter(
                "has_key",
                bool,
                required=False,
                description="Only return certificate-key pairs with keys",
            ),
            OpenApiParameter("include_details", bool, default=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @permission_required(None, ["authentik_crypto.add_certificatekeypair"])
    @extend_schema(
        request=CertificateGenerationSerializer(),
        responses={
            200: CertificateKeyPairSerializer,
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=False, methods=["POST"])
    def generate(self, request: Request) -> Response:
        """Generate a new, self-signed certificate-key pair"""
        data = CertificateGenerationSerializer(data=request.data)
        if not data.is_valid():
            return Response(data.errors, status=400)
        raw_san = data.validated_data.get("subject_alt_name", "")
        sans = raw_san.split(",") if raw_san != "" else []
        builder = CertificateBuilder(data.validated_data["common_name"])
        builder.build(
            subject_alt_names=sans,
            validity_days=int(data.validated_data["validity_days"]),
        )
        instance = builder.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="download",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            )
        ],
        responses={200: CertificateDataSerializer(many=False)},
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    def view_certificate(self, request: Request, pk: str) -> Response:
        """Return certificate-key pairs certificate and log access"""
        certificate: CertificateKeyPair = self.get_object()
        Event.new(  # noqa # nosec
            EventAction.SECRET_VIEW,
            secret=certificate,
            type="certificate",
        ).from_http(request)
        if "download" in request.query_params:
            # Mime type from https://pki-tutorial.readthedocs.io/en/latest/mime.html
            response = HttpResponse(
                certificate.certificate_data, content_type="application/x-pem-file"
            )
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{certificate.name}_certificate.pem"'
            return response
        return Response(CertificateDataSerializer({"data": certificate.certificate_data}).data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="download",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            )
        ],
        responses={200: CertificateDataSerializer(many=False)},
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    def view_private_key(self, request: Request, pk: str) -> Response:
        """Return certificate-key pairs private key and log access"""
        certificate: CertificateKeyPair = self.get_object()
        Event.new(  # noqa # nosec
            EventAction.SECRET_VIEW,
            secret=certificate,
            type="private_key",
        ).from_http(request)
        if "download" in request.query_params:
            # Mime type from https://pki-tutorial.readthedocs.io/en/latest/mime.html
            response = HttpResponse(certificate.key_data, content_type="application/x-pem-file")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="{certificate.name}_private_key.pem"'
            return response
        return Response(CertificateDataSerializer({"data": certificate.key_data}).data)
