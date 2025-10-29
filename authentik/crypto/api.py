"""Crypto API Views"""

from datetime import datetime

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.dsa import (
    DSAPrivateKey,
    DSAPublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed448 import (
    Ed448PrivateKey,
    Ed448PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from django.http.response import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from django_filters.filters import BooleanFilter, MultipleChoiceFilter
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    CharField,
    ChoiceField,
    DateTimeField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.validators import UniqueValidator
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import UserTypes
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.builder import CertificateBuilder, PrivateKeyAlg
from authentik.crypto.models import CertificateKeyPair, KeyType
from authentik.events.models import Event, EventAction
from authentik.rbac.decorators import permission_required
from authentik.rbac.filters import ObjectFilter, SecretKeyFilter

LOGGER = get_logger()


def get_key_type_from_key(key) -> str | None:
    """Determine key type using isinstance checks.

    Works with both private and public keys from cryptography library.
    Returns the KeyType enum value, or None for unknown types.
    """
    if isinstance(key, RSAPrivateKey | RSAPublicKey):
        return KeyType.RSA
    if isinstance(key, EllipticCurvePrivateKey | EllipticCurvePublicKey):
        return KeyType.EC
    if isinstance(key, DSAPrivateKey | DSAPublicKey):
        return KeyType.DSA
    if isinstance(key, Ed25519PrivateKey | Ed25519PublicKey):
        return KeyType.ED25519
    if isinstance(key, Ed448PrivateKey | Ed448PublicKey):
        return KeyType.ED448
    return None


class CertificateKeyPairSerializer(ModelSerializer):
    """CertificateKeyPair Serializer"""

    fingerprint_sha256 = SerializerMethodField()
    fingerprint_sha1 = SerializerMethodField()

    cert_expiry = SerializerMethodField()
    cert_subject = SerializerMethodField()
    private_key_available = SerializerMethodField()
    key_type = SerializerMethodField()

    certificate_download_url = SerializerMethodField()
    private_key_download_url = SerializerMethodField()

    @property
    def _should_include_details(self) -> bool:
        request: Request = self.context.get("request", None)
        if not request:
            return True
        return str(request.query_params.get("include_details", "true")).lower() == "true"

    def get_fingerprint_sha256(self, instance: CertificateKeyPair) -> str | None:
        "Get certificate Hash (SHA256)"
        if not self._should_include_details:
            return None
        return instance.fingerprint_sha256

    def get_fingerprint_sha1(self, instance: CertificateKeyPair) -> str | None:
        "Get certificate Hash (SHA1)"
        if not self._should_include_details:
            return None
        return instance.fingerprint_sha1

    def get_cert_expiry(self, instance: CertificateKeyPair) -> datetime | None:
        "Get certificate expiry"
        if not self._should_include_details:
            return None
        return DateTimeField().to_representation(instance.certificate.not_valid_after_utc)

    def get_cert_subject(self, instance: CertificateKeyPair) -> str | None:
        """Get certificate subject as full rfc4514"""
        if not self._should_include_details:
            return None
        return instance.certificate.subject.rfc4514_string()

    def get_private_key_available(self, instance: CertificateKeyPair) -> bool:
        """Show if this keypair has a private key configured or not"""
        return instance.key_data != "" and instance.key_data is not None

    @extend_schema_field(ChoiceField(choices=KeyType.choices, allow_null=True))
    def get_key_type(self, instance: CertificateKeyPair) -> str | None:
        """Get the key algorithm type from the certificate's public key"""
        if not self._should_include_details:
            return None
        public_key = instance.certificate.public_key()
        return get_key_type_from_key(public_key)

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
            raise ValidationError("Unable to load certificate.") from None
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
                raise ValidationError("Unable to load private key (possibly encrypted?).") from None
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
            "key_type",
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

    common_name = CharField(
        validators=[UniqueValidator(queryset=CertificateKeyPair.objects.all())],
        source="name",
    )
    subject_alt_name = CharField(required=False, allow_blank=True, label=_("Subject-alt name"))
    validity_days = IntegerField(initial=365)
    alg = ChoiceField(default=PrivateKeyAlg.RSA, choices=PrivateKeyAlg.choices)


class CertificateKeyPairFilter(FilterSet):
    """Filter for certificates"""

    has_key = BooleanFilter(
        label="Only return certificate-key pairs with keys", method="filter_has_key"
    )

    key_type = MultipleChoiceFilter(
        choices=KeyType.choices,
        label="Filter by key algorithm type",
        method="filter_key_type",
    )

    def filter_has_key(self, queryset, name, value):  # pragma: no cover
        """Only return certificate-key pairs with keys"""
        if not value:
            return queryset
        return queryset.exclude(key_data__exact="")

    def filter_key_type(self, queryset, name, value):  # pragma: no cover
        """Filter certificates by key type using the public key from the certificate"""
        if not value:
            return queryset

        # value is a list of KeyType enum values from MultipleChoiceFilter
        filtered_pks = []
        for cert in queryset:

            public_key = cert.certificate.public_key()
            key_type = get_key_type_from_key(public_key)

            if key_type and key_type in value:
                filtered_pks.append(cert.pk)

        return queryset.filter(pk__in=filtered_pks)

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
            OpenApiParameter(
                "key_type",
                OpenApiTypes.STR,
                required=False,
                many=True,
                enum=[choice[0] for choice in KeyType.choices],
                description=(
                    "Filter by key algorithm type (RSA, EC, DSA, etc). "
                    "Can be specified multiple times (e.g. '?key_type=rsa&key_type=ec')"
                ),
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
        data.is_valid(raise_exception=True)
        raw_san = data.validated_data.get("subject_alt_name", "")
        sans = raw_san.split(",") if raw_san != "" else []
        builder = CertificateBuilder(data.validated_data["name"])
        builder.alg = data.validated_data["alg"]
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
    @action(detail=True, pagination_class=None, filter_backends=[ObjectFilter])
    def view_certificate(self, request: Request, pk: str) -> Response:
        """Return certificate-key pairs certificate and log access"""
        certificate: CertificateKeyPair = self.get_object()
        if request.user.type != UserTypes.INTERNAL_SERVICE_ACCOUNT:
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
            response["Content-Disposition"] = (
                f'attachment; filename="{certificate.name}_certificate.pem"'
            )
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
    @action(detail=True, pagination_class=None, filter_backends=[ObjectFilter])
    def view_private_key(self, request: Request, pk: str) -> Response:
        """Return certificate-key pairs private key and log access"""
        certificate: CertificateKeyPair = self.get_object()
        if request.user.type != UserTypes.INTERNAL_SERVICE_ACCOUNT:
            Event.new(  # noqa # nosec
                EventAction.SECRET_VIEW,
                secret=certificate,
                type="private_key",
            ).from_http(request)
        if "download" in request.query_params:
            # Mime type from https://pki-tutorial.readthedocs.io/en/latest/mime.html
            response = HttpResponse(certificate.key_data, content_type="application/x-pem-file")
            response["Content-Disposition"] = (
                f'attachment; filename="{certificate.name}_private_key.pem"'
            )
            return response
        return Response(CertificateDataSerializer({"data": certificate.key_data}).data)
