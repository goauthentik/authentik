from django.db import models
from rest_framework.serializers import Serializer

from authentik.endpoints.models import Connector


class AgentConnector(Connector):

    enroll_secret = models.TextField()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.agent.api.connector import (
            AgentConnectorSerializer,
        )

        return AgentConnectorSerializer


# class AgentDeviceConnection(DeviceConnection):

#     pass
