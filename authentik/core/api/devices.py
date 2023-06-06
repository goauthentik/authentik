"""Authenticator Devices API Views"""
from django.conf import settings
from django_otp import device_classes, devices_for_user
from django_otp.models import Device
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, IntegerField, SerializerMethodField
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.crypto.tasks import generate_pre_shared_key
from authentik.core.api.utils import MetaNameSerializer
from authentik.core.models import User

import json
import time


class DeviceSerializer(MetaNameSerializer):
    """Serializer for Duo authenticator devices"""

    pk = IntegerField()
    name = CharField()
    type = SerializerMethodField()
    confirmed = BooleanField()

    def get_type(self, instance: Device) -> str:
        """Get type of device"""
        return instance._meta.label


class DeviceViewSet(ViewSet):
    """Viewset for authenticator devices"""

    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: DeviceSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Get all devices for current user"""
        devices = devices_for_user(request.user)
        return Response(DeviceSerializer(devices, many=True).data)


class AdminDeviceViewSet(ViewSet):
    """Viewset for authenticator devices"""

    serializer_class = DeviceSerializer
    permission_classes = [IsAdminUser]

    def get_devices(self, **kwargs):
        """Get all devices in all child classes"""
        for model in device_classes():
            device_set = model.objects.filter(**kwargs)
            yield from device_set

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
            )
        ],
        responses={200: DeviceSerializer(many=True)},
    )
    def list(self, request: Request) -> Response:
        """Get all devices for current user"""
        kwargs = {}
        if "user" in request.query_params:
            kwargs = {"user": request.query_params["user"]}
        return Response(DeviceSerializer(self.get_devices(**kwargs), many=True).data)


@action(detail=False, methods=['get'])
def get_qr_code_data(self, request: Request) -> Response:
    """
    Returns the necessary data for the QR code for the Authentik server URL,
    pre-shared key, and expiration timestamp.
    """
    pre_shared_key = generate_pre_shared_key()
    server_url = request.build_absolute_uri('/')
    expiration_timestamp = int(time.time()) + 60*60*24  # Expires in 24 hours
    
    qr_data = {
        'server_url': server_url,
        'pre_shared_key': pre_shared_key,
        'expiration_timestamp': expiration_timestamp,
    }
    
    return Response(json.dumps(qr_data))


@action(detail=False, methods=['post'])
def save_device_info(self, request: Request) -> Response:
    """
    Saves device information and returns server configuration data.
    """
    # Fetch pre-shared key and device identifier from request data
    pre_shared_key = request.data.get('pre_shared_key')
    device_identifier = request.data.get('device_identifier')

    # Validate pre-shared key (the exact method of validation will depend on your application requirements)

    # Here, I'm assuming a User model has a ForeignKey field called `device` linked to a Device model.
    # Modify this according to your actual model structures.
    user = User.objects.get(device__identifier=device_identifier)

    if not user:
        return Response({'error': 'Invalid device identifier.'}, status=400)

    # Fetch the branding details, miscellaneous settings, and TOTP secret
    # The exact method of fetching these data will depend on your application.
    branding_details = settings.BRANDING_DETAILS
    misc_settings = settings.MISC_SETTINGS
    totp_secret = user.totp_secret

    # Send the branding details, misc settings, and TOTP secret to the mobile app
    return Response({
        'branding_details': branding_details,
        'misc_settings': misc_settings,
        'totp_secret': totp_secret,
    })
