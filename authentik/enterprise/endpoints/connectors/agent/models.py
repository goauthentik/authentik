from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector


class AgentConnector(Connector):

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.agent.api.connector import (
            AgentConnectorSerializer,
        )

        return AgentConnectorSerializer


# class AgentDeviceConnection(DeviceConnection):

#     pass
