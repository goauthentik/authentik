"""RAC Connection override API Views"""

from uuid import uuid4

from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.models import Device, DeviceAccessGroup
from authentik.providers.rac.models import RACConnectionOverride


class RACConnectionOverrideSerializer(ModelSerializer):
    """RACConnectionOverride Serializer"""

    name = CharField(source="device.name", read_only=True)
    device_name = CharField(
        write_only=True,
        required=False,
        help_text="Name of the device to create. Only used when no device is set.",
    )
    access_group = PrimaryKeyRelatedField(
        queryset=DeviceAccessGroup.objects.all(),
        write_only=True,
        required=False,
        help_text="Access group of the device to create. Only used when no device is set.",
    )

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        if not self.instance and not attrs.get("device") and not attrs.get("device_name"):
            raise ValidationError({"device": "Either device or device_name must be set."})
        return attrs

    def create(self, validated_data: dict) -> RACConnectionOverride:
        device_name = validated_data.pop("device_name", None)
        access_group = validated_data.pop("access_group", None)
        if not validated_data.get("device"):
            # Devices which are not enrolled through a connector are created along with
            # the override which says how to reach them
            validated_data["device"] = Device.objects.create(
                name=device_name,
                identifier=f"rac://{uuid4()}",
                expiring=False,
                access_group=access_group,
            )
        return super().create(validated_data)

    def update(
        self, instance: RACConnectionOverride, validated_data: dict
    ) -> RACConnectionOverride:
        device_name = validated_data.pop("device_name", None)
        validated_data.pop("access_group", None)
        if device_name and device_name != instance.device.name:
            instance.device.name = device_name
            instance.device.save(update_fields=["name"])
        return super().update(instance, validated_data)

    class Meta:
        model = RACConnectionOverride
        fields = [
            "pk",
            "name",
            "device",
            "device_name",
            "access_group",
            "host",
            "protocol",
        ]
        extra_kwargs = {
            "device": {"required": False},
        }


class RACConnectionOverrideViewSet(UsedByMixin, ModelViewSet):
    """RACConnectionOverride Viewset"""

    queryset = RACConnectionOverride.objects.all().select_related("device")
    serializer_class = RACConnectionOverrideSerializer
    filterset_fields = ["device", "protocol"]
    search_fields = ["device__name", "host"]
    ordering = ["device__name"]
