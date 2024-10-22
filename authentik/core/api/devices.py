"""Authenticator Devices API Views"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.fields import (
    BooleanField,
    CharField,
    DateTimeField,
    IntegerField,
    SerializerMethodField,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.core.api.utils import MetaNameSerializer
from authentik.rbac.decorators import permission_required
from authentik.stages.authenticator import device_classes, devices_for_user
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class DeviceSerializer(MetaNameSerializer):
    """Serializer for Duo authenticator devices"""

    pk = IntegerField()
    name = CharField()
    type = SerializerMethodField()
    confirmed = BooleanField()
    created = DateTimeField(read_only=True)
    last_updated = DateTimeField(read_only=True)
    last_used = DateTimeField(read_only=True, allow_null=True)
    extra_description = SerializerMethodField()

    def get_type(self, instance: Device) -> str:
        """Get type of device"""
        return instance._meta.label

    def get_extra_description(self, instance: Device) -> str:
        """Get extra description"""
        if isinstance(instance, WebAuthnDevice):
            return instance.device_type.description
        return ""


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
    permission_classes = []

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
    @permission_required(
        None,
        [f"{model._meta.app_label}.view_{model._meta.model_name}" for model in device_classes()],
    )
    def list(self, request: Request) -> Response:
        """Get all devices for current user"""
        kwargs = {}
        if "user" in request.query_params:
            kwargs = {"user": request.query_params["user"]}
        return Response(DeviceSerializer(self.get_devices(**kwargs), many=True).data)
