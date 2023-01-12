"""RAC Models"""
from django.db import models
from rest_framework.serializers import Serializer

from authentik.core.models import Provider


class Protocols(models.TextChoices):
    """Supported protocols"""

    RDP = "rdp"
    VNC = "vnc"
    SSH = "ssh"


class AuthenticationMode(models.TextChoices):
    """"""

    STATIC = "static"
    PROMPT = "prompt"


class RACProvider(Provider):
    """Remote access provider"""

    protocol = models.TextField(choices=Protocols.choices)
    host = models.TextField()
    settings = models.JSONField(default=dict)
    auth_mode = models.TextField(choices=AuthenticationMode.choices)

    # self.client.handshake(
    #     protocol="rdp",
    #     hostname="10.120.20.57",
    #     port=3389,
    #     security="any",
    #     ignore_cert="true",
    # )

    @property
    def component(self) -> str:
        return "ak-provider-rac-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.rac.api.providers import RACProviderSerializer

        return RACProviderSerializer
