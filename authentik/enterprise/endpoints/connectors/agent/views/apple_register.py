from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.api.validation import validate
from authentik.core.api.users import UserSelfSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.endpoints.connectors.agent.models import (
    AgentDeviceConnection,
    AgentDeviceUserBinding,
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

        user_secure_enclave_key = CharField()
        enclave_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = AgentPSSOUserRegistration
    authentication_classes = [AgentAuth]

    @extend_schema(
        responses={
            200: UserSelfSerializer(),
        }
    )
    @validate(AgentPSSOUserRegistration)
    def post(self, request: Request, body: AgentPSSOUserRegistration) -> Response:
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        AgentDeviceUserBinding.objects.update_or_create(
            device=conn.device,
            user=request.user,
            create_defaults={
                "is_primary": True,
            },
            defaults={
                "apple_secure_enclave_key": body.validated_data["user_secure_enclave_key"],
                "apple_enclave_key_id": body.validated_data["enclave_key_id"],
            },
        )
        context = {"request": request}
        return Response(UserSelfSerializer(instance=request.user, context=context).data)
