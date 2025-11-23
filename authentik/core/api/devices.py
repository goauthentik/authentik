"""Authenticator Devices API Views"""

from drf_spectacular.utils import extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    SerializerMethodField,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.core.api.users import ParamUserSerializer
from authentik.core.api.utils import MetaNameSerializer
from authentik.enterprise.stages.authenticator_endpoint_gdtc.models import EndpointDevice
from authentik.stages.authenticator import device_classes, devices_for_user
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class DeviceSerializer(MetaNameSerializer):
    """Serializer for authenticator devices"""

    pk = CharField()
    name = CharField()
    type = SerializerMethodField()
    confirmed = BooleanField()
    created = DateTimeField(read_only=True)
    last_updated = DateTimeField(read_only=True)
    last_used = DateTimeField(read_only=True, allow_null=True)
    extra_description = SerializerMethodField()
    external_id = SerializerMethodField()

    def get_type(self, instance: Device) -> str:
        """Get type of device"""
        return instance._meta.label

    def get_extra_description(self, instance: Device) -> str | None:
        """Get extra description"""
        if isinstance(instance, WebAuthnDevice):
            return instance.device_type.description if instance.device_type else None
        if isinstance(instance, EndpointDevice):
            return instance.data.get("deviceSignals", {}).get("deviceModel")
        return None

    def get_external_id(self, instance: Device) -> str | None:
        """Get external Device ID"""
        if isinstance(instance, WebAuthnDevice):
            return instance.device_type.aaguid if instance.device_type else None
        if isinstance(instance, EndpointDevice):
            return instance.data.get("deviceSignals", {}).get("deviceModel")
        return None


class DeviceViewSet(ViewSet):
    """Viewset for authenticator devices"""

    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request: Request) -> Response:
        """Get all devices for current user"""
        devices = devices_for_user(request.user)
        return Response(DeviceSerializer(devices, many=True).data)


class AdminDeviceViewSet(ViewSet):
    """Viewset for authenticator devices"""

    serializer_class = DeviceSerializer
    permission_classes = []

    def get_devices(self, **kwargs):
        """Get all devices in all child classes"""
        for model in device_classes():
            device_set = get_objects_for_user(
                self.request.user, f"{model._meta.app_label}.view_{model._meta.model_name}"
            ).filter(**kwargs)
            yield from device_set

    @extend_schema(
        parameters=[ParamUserSerializer],
        responses={200: DeviceSerializer(many=True)},
    )
    def list(self, request: Request) -> Response:
        """Get all devices for current user"""
        args = ParamUserSerializer(data=request.query_params)
        args.is_valid(raise_exception=True)
        return Response(DeviceSerializer(self.get_devices(**args.validated_data), many=True).data)
