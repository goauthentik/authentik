from rest_framework.fields import SerializerMethodField

from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.api.device_fact_snapshots import DeviceFactSnapshotSerializer
from authentik.endpoints.models import DeviceConnection


class DeviceConnectionSerializer(ModelSerializer):

    connector_obj = ConnectorSerializer(source="connector", read_only=True)
    latest_snapshot = SerializerMethodField()

    def get_latest_snapshot(
        self, instance: DeviceConnection
    ) -> DeviceFactSnapshotSerializer:
        return DeviceFactSnapshotSerializer(
            instance.devicefactsnapshot_set.order_by("-created").first()
        )

    class Meta:
        model = DeviceConnection
        fields = ["device", "connector", "connector_obj", "latest_snapshot",]
