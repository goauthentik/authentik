"""Authenticator Devices API Views"""
from django_otp import devices_for_user
from django_otp.models import Device
from drf_spectacular.utils import extend_schema
from rest_framework.fields import CharField, IntegerField, SerializerMethodField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.core.api.utils import MetaNameSerializer


class DeviceSerializer(MetaNameSerializer):
    """Serializer for Duo authenticator devices"""

    pk = IntegerField()
    name = CharField()
    type = SerializerMethodField()

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
