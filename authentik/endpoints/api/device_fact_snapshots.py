from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.facts import DeviceFacts
from authentik.endpoints.models import DeviceFactSnapshot


class DeviceFactSnapshotSerializer(ModelSerializer):

    data = DeviceFacts()

    class Meta:
        model = DeviceFactSnapshot
        fields = [
            "data",
            "connection",
            "created",
            "expires",
        ]
        extra_kwargs = {
            "created": {"read_only": True},
            "expires": {"read_only": True},
        }
