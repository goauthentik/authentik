"""Interface models"""
from typing import Type
from uuid import uuid4

from django.db import models
from rest_framework.serializers import BaseSerializer

from authentik.lib.models import SerializerModel


class InterfaceType(models.TextChoices):
    """Interface types"""

    USER = "user"
    ADMIN = "admin"
    FLOW = "flow"


class Interface(SerializerModel):
    """Interface"""

    interface_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    url_name = models.SlugField()

    type = models.TextField(choices=InterfaceType.choices)
    template = models.TextField()

    @property
    def serializer(self) -> Type[BaseSerializer]:
        from authentik.interfaces.api import InterfaceSerializer

        return InterfaceSerializer
