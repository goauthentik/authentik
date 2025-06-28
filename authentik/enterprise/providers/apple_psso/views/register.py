from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import BaseAuthentication
from rest_framework.fields import CharField
from rest_framework.relations import StringRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.api.authentication import TokenAuthentication
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import User
from authentik.enterprise.providers.apple_psso.models import (
    AppleDevice,
    AppleDeviceUser,
    ApplePlatformSSOProvider,
)
from authentik.lib.generators import generate_key


class DeviceRegisterAuth(BaseAuthentication):
    def authenticate(self, request):
        # very temporary, lol
        return (User(), None)


class RegisterDeviceView(APIView):

    class DeviceRegistration(PassiveSerializer):

        device_uuid = CharField()
        client_id = CharField()
        device_signing_key = CharField()
        device_encryption_key = CharField()
        sign_key_id = CharField()
        enc_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = DeviceRegistration
    authentication_classes = [DeviceRegisterAuth, TokenAuthentication]

    def post(self, request: Request) -> Response:
        data = self.DeviceRegistration(data=request.data)
        data.is_valid(raise_exception=True)
        provider = get_object_or_404(
            ApplePlatformSSOProvider, client_id=data.validated_data["client_id"]
        )
        AppleDevice.objects.update_or_create(
            endpoint_uuid=data.validated_data["device_uuid"],
            defaults={
                "signing_key": data.validated_data["device_signing_key"],
                "encryption_key": data.validated_data["device_encryption_key"],
                "sign_key_id": data.validated_data["sign_key_id"],
                "enc_key_id": data.validated_data["enc_key_id"],
                "key_exchange_key": generate_key(),
                "provider": provider,
            },
        )
        return Response()


class RegisterUserView(APIView):

    class UserRegistration(PassiveSerializer):

        device_uuid = CharField()
        user_id = CharField()
        user_signing_key = CharField()
        user_encryption_key = CharField()
        sign_key_id = CharField()
        enc_key_id = CharField()

    permission_classes = []
    pagination_class = None
    filter_backends = []
    serializer_class = UserRegistration
    authentication_classes = [TokenAuthentication]

    def post(self, request: Request) -> Response:
        data = self.UserRegistration(data=request.data)
        data.is_valid(raise_exception=True)
        device = get_object_or_404(AppleDevice, endpoint_uuid=data.validated_data["device_uuid"])
        user = get_object_or_404(User, username=data.validated_data["user_id"])
        AppleDeviceUser.objects.update_or_create(
            device=device,
            user=user,
            defaults={
                "signing_key": data.validated_data["user_signing_key"],
                "encryption_key": data.validated_data["user_encryption_key"],
                "sign_key_id": data.validated_data["sign_key_id"],
                "enc_key_id": data.validated_data["enc_key_id"],
            },
        )
        return Response()
