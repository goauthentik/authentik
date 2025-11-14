from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.models import DeviceConnection


class DeviceConnectionSerializer(ModelSerializer):

    connector_obj = ConnectorSerializer(source="connector", read_only=True)

    class Meta:
        model = DeviceConnection
        fields = [
            "device",
            "connector",
            "connector_obj",
            "data",
            "last_update",
        ]
