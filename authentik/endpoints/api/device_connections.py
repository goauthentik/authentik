from rest_framework.fields import SerializerMethodField

from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.api.device_fact_snapshots import DeviceFactSnapshotSerializer
from authentik.endpoints.models import Connector, DeviceConnection, DeviceFactSnapshot


class DeviceConnectionSerializer(ModelSerializer):

    connector_obj = ConnectorSerializer(source="connector", read_only=True)
    latest_snapshot = SerializerMethodField(allow_null=True)

    def get_latest_snapshot(self, instance: DeviceConnection) -> DeviceFactSnapshotSerializer:
        snapshot: DeviceFactSnapshot | None = instance.devicefactsnapshot_set.order_by(
            "-created"
        ).first()
        if not snapshot:
            return None
        connector: Connector = Connector.objects.get_subclass(pk=snapshot.connection.connector_id)
        vendor = connector.controller.vendor_identifier()
        return DeviceFactSnapshotSerializer(
            snapshot,
            context={
                "vendor": vendor,
            },
        ).data

    class Meta:
        model = DeviceConnection
        fields = [
            "device",
            "connector",
            "connector_obj",
            "latest_snapshot",
        ]
