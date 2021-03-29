"""Crypto API Views"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509 import load_pem_x509_certificate
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    DateTimeField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair
from authentik.events.models import Event, EventAction


class CertificateKeyPairSerializer(ModelSerializer):
    """CertificateKeyPair Serializer"""

    cert_expiry = DateTimeField(source="certificate.not_valid_after", read_only=True)
    cert_subject = SerializerMethodField()
    private_key_available = SerializerMethodField()

    def get_cert_subject(self, instance: CertificateKeyPair) -> str:
        """Get certificate subject as full rfc4514"""
        return instance.certificate.subject.rfc4514_string()

    def get_private_key_available(self, instance: CertificateKeyPair) -> bool:
        """Show if this keypair has a private key configured or not"""
        return instance.key_data != "" and instance.key_data is not None

    def validate_certificate_data(self, value):
        """Verify that input is a valid PEM x509 Certificate"""
        try:
            load_pem_x509_certificate(value.encode("utf-8"), default_backend())
        except ValueError:
            raise ValidationError("Unable to load certificate.")
        return value

    def validate_key_data(self, value):
        """Verify that input is a valid PEM RSA Key"""
        # Since this field is optional, data can be empty.
        if value != "":
            try:
                load_pem_private_key(
                    str.encode("\n".join([x.strip() for x in value.split("\n")])),
                    password=None,
                    backend=default_backend(),
                )
            except ValueError:
                raise ValidationError("Unable to load private key.")
        return value

    class Meta:

        model = CertificateKeyPair
        fields = [
            "pk",
            "name",
            "fingerprint",
            "certificate_data",
            "key_data",
            "cert_expiry",
            "cert_subject",
            "private_key_available",
        ]
        extra_kwargs = {
            "key_data": {"write_only": True},
            "certificate_data": {"write_only": True},
        }


class CertificateDataSerializer(Serializer):
    """Get CertificateKeyPair's data"""

    data = CharField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class CertificateGenerationSerializer(Serializer):
    """Certificate generation parameters"""

    common_name = CharField()
    subject_alt_name = CharField(
        required=False, allow_blank=True, label=_("Subject-alt name")
    )
    validity_days = IntegerField(initial=365)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class CertificateKeyPairViewSet(ModelViewSet):
    """CertificateKeyPair Viewset"""

    queryset = CertificateKeyPair.objects.all()
    serializer_class = CertificateKeyPairSerializer

    @permission_required(None, "authentik_crypto.add_certificatekeypair")
    @swagger_auto_schema(
        request_body=CertificateGenerationSerializer(),
        responses={200: CertificateKeyPairSerializer},
    )
    @action(detail=False, methods=["POST"])
    def generate(self, request: Request) -> Response:
        """Generate a new, self-signed certificate-key pair"""
        data = CertificateGenerationSerializer(data=request.data)
        if not data.is_valid():
            return Response(data.errors, status=400)
        builder = CertificateBuilder()
        builder.common_name = data.validated_data["common_name"]
        builder.build(
            subject_alt_names=data.validated_data.get("subject_alt_name", "").split(
                ","
            ),
            validity_days=int(data.validated_data["validity_days"]),
        )
        instance = builder.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: CertificateDataSerializer(many=False)})
    @action(detail=True)
    # pylint: disable=invalid-name, unused-argument
    def view_certificate(self, request: Request, pk: str) -> Response:
        """Return certificate-key pairs certificate and log access"""
        certificate: CertificateKeyPair = self.get_object()
        Event.new(  # noqa # nosec
            EventAction.SECRET_VIEW,
            secret=certificate,
            type="certificate",
        ).from_http(request)
        return Response(
            CertificateDataSerializer({"data": certificate.certificate_data}).data
        )

    @swagger_auto_schema(responses={200: CertificateDataSerializer(many=False)})
    @action(detail=True)
    # pylint: disable=invalid-name, unused-argument
    def view_private_key(self, request: Request, pk: str) -> Response:
        """Return certificate-key pairs private key and log access"""
        certificate: CertificateKeyPair = self.get_object()
        Event.new(  # noqa # nosec
            EventAction.SECRET_VIEW,
            secret=certificate,
            type="private_key",
        ).from_http(request)
        return Response(CertificateDataSerializer({"data": certificate.key_data}).data)
