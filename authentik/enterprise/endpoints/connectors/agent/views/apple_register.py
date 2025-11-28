from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.api.authentication import TokenAuthentication
from authentik.core.api.users import UserSelfSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    AgentDeviceConnection,
    AgentDeviceUserBinding,
)
from authentik.endpoints.models import Device
from authentik.lib.generators import generate_key


class RegisterDeviceView(APIView):

    class DeviceRegistration(PassiveSerializer):

        identifier = CharField()
        client_id = CharField()
        device_signing_key = CharField()
        device_encryption_key = CharField()
        sign_key_id = CharField()
        enc_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = DeviceRegistration
    authentication_classes = [TokenAuthentication]

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Device registered"),
        }
    )
    def post(self, request: Request) -> Response:
        data = self.DeviceRegistration(data=request.data)
        data.is_valid(raise_exception=True)
        connector = get_object_or_404(AgentConnector, token__user__in=[request.user])
        device, _ = Device.objects.get_or_create(
            identifier=data.validated_data["identifier"],
        )
        AgentDeviceConnection.objects.update_or_create(
            device=device,
            connector=connector,
            defaults={
                "signing_key": data.validated_data["device_signing_key"],
                "encryption_key": data.validated_data["device_encryption_key"],
                "sign_key_id": data.validated_data["sign_key_id"],
                "enc_key_id": data.validated_data["enc_key_id"],
                "key_exchange_key": generate_key(),
            },
        )
        return Response(status=204)


class RegisterUserView(APIView):

    class UserRegistration(PassiveSerializer):

        identifier = CharField()
        user_secure_enclave_key = CharField()
        enclave_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = UserRegistration
    authentication_classes = [TokenAuthentication]

    @extend_schema(
        responses={
            200: UserSelfSerializer(),
        }
    )
    def post(self, request: Request) -> Response:
        data = self.UserRegistration(data=request.data)
        data.is_valid(raise_exception=True)
        device = get_object_or_404(Device, identifier=data.validated_data["identifier"])
        AgentDeviceUserBinding.objects.update_or_create(
            device=device,
            user=request.user,
            create_defaults={
                "is_primary": True,
            },
            defaults={
                "secure_enclave_key": data.validated_data["user_secure_enclave_key"],
                "enclave_key_id": data.validated_data["enclave_key_id"],
            },
        )
        context = {"request": request}
        return Response(UserSelfSerializer(instance=request.user, context=context).data)
