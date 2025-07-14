from django.db import models

from authentik.core.models import ExpiringModel
from authentik.endpoints.models import DeviceConnection, DeviceUser, EndpointConnector


class ApplePlatformSSOConnector(EndpointConnector):

    @property
    def serializer(self):
        from authentik.enterprise.endpoints.apple_psso.api.connectors import (
            ApplePlatformSSOConnectorSerializer,
        )

        return ApplePlatformSSOConnectorSerializer


class AppleDeviceConnection(DeviceConnection):

    signing_key = models.TextField()
    encryption_key = models.TextField()
    key_exchange_key = models.TextField()
    sign_key_id = models.TextField()
    enc_key_id = models.TextField()

    @property
    def serializer(self):
        from authentik.enterprise.endpoints.apple_psso.api.connections import (
            AppleDeviceConnectionSerializer,
        )

        return AppleDeviceConnectionSerializer


class AppleDeviceUser(DeviceUser):
    secure_enclave_key = models.TextField()
    enclave_key_id = models.TextField()

    @property
    def serializer(self):
        from authentik.enterprise.endpoints.apple_psso.api.users import (
            AppleDeviceUserSerializer,
        )

        return AppleDeviceUserSerializer


class AppleNonce(ExpiringModel):
    nonce = models.TextField()
