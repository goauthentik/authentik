from authentik.core.api.utils import MetaNameSerializer
from authentik.endpoints.models import Connector


class ConnectorSerializer(MetaNameSerializer):

    class Meta:
        model = Connector
        fields = [
            "connector_uuid",
            "name",
        ]
