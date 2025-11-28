from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.api.validation import validate
from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.endpoints.connectors.agent.models import (
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    DeviceAuthenticationToken,
    DeviceToken,
)
from authentik.lib.generators import generate_key


class RegisterDeviceView(APIView):

    class AgentPSSODeviceRegistration(PassiveSerializer):

        client_id = CharField()
        device_signing_key = CharField()
        device_encryption_key = CharField()
        sign_key_id = CharField()
        enc_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = AgentPSSODeviceRegistration
    authentication_classes = [AgentAuth]

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Device registered"),
        }
    )
    @validate(AgentPSSODeviceRegistration)
    def post(self, request: Request, body: AgentPSSODeviceRegistration) -> Response:
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        conn.apple_signing_key = body.validated_data["device_signing_key"]
        conn.apple_encryption_key = body.validated_data["device_encryption_key"]
        conn.apple_sign_key_id = body.validated_data["sign_key_id"]
        conn.apple_enc_key_id = body.validated_data["enc_key_id"]
        conn.apple_key_exchange_key = generate_key()
        conn.save()
        return Response(status=204)


class RegisterUserView(APIView):

    class AgentPSSOUserRegistration(PassiveSerializer):

        user_auth = CharField()
        user_secure_enclave_key = CharField()
        enclave_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = AgentPSSOUserRegistration
    authentication_classes = [AgentAuth]

    @extend_schema(
        responses={
            204: OpenApiResponse(description="User successfully registered"),
        }
    )
    @validate(AgentPSSOUserRegistration)
    def post(self, request: Request, body: AgentPSSOUserRegistration) -> Response:
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        user_token = DeviceAuthenticationToken.filter_not_expired(
            device=conn.device, token=body.validated_data["user_auth"]
        ).first()
        if not user_token:
            raise ValidationError("Invalid user authentication")
        AgentDeviceUserBinding.objects.update_or_create(
            device=conn.device,
            user=user_token.user,
            connector=conn.connector,
            create_defaults={
                "is_primary": True,
                "order": 0,
            },
            defaults={
                "apple_secure_enclave_key": body.validated_data["user_secure_enclave_key"],
                "apple_enclave_key_id": body.validated_data["enclave_key_id"],
            },
        )
        return Response(status=204)
