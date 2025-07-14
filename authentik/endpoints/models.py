from uuid import uuid4

from django.db import models
from django.utils.functional import cached_property
from rest_framework.serializers import Serializer

from authentik.core.models import Token, User
from authentik.endpoints.facts.view import FactsView
from authentik.lib.models import SerializerModel


class Device(SerializerModel):
    device_uuid = models.UUIDField(default=uuid4)

    identifier = models.TextField(unique=True)
    users = models.ManyToManyField(User, through="DeviceUser")
    connections = models.ManyToManyField("EndpointConnector", through="DeviceConnection")

    @cached_property
    def facts(self) -> FactsView:
        pass

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.endpoints.api.devices import DeviceSerializer

        return DeviceSerializer


class DeviceUser(SerializerModel):
    device_user_uuid = models.UUIDField(default=uuid4)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_primary = models.BooleanField()

    @property
    def serializer(self) -> type[Serializer]:
        raise NotImplementedError


class DeviceConnection(SerializerModel):
    device_connection_uuid = models.UUIDField(default=uuid4)
    device = models.ForeignKey("Device", on_delete=models.CASCADE)
    connector = models.ForeignKey("EndpointConnector", on_delete=models.CASCADE)
    facts = models.JSONField(default=list, help_text="Facts gathered by this connector")

    @property
    def serializer(self) -> type[Serializer]:
        raise NotImplementedError


class EndpointConnector(SerializerModel):
    connector_uuid = models.UUIDField(default=uuid4)

    name = models.TextField()

    tokens = models.ManyToManyField(Token)

    @property
    def serializer(self) -> type[Serializer]:
        raise NotImplementedError
