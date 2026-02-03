from django.db import models
from rest_framework.fields import (
    BooleanField,
    CharField,
    IntegerField,
    SerializerMethodField,
)

from authentik.api.v3.config import ConfigSerializer, ConfigView
from authentik.brands.api import CurrentBrandSerializer
from authentik.brands.models import Brand
from authentik.core.api.utils import PassiveSerializer
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.endpoints.models import Device
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.views.jwks import JWKSView

try:
    from authentik.enterprise.models import LicenseUsageStatus
except ImportError:

    class LicenseUsageStatus(models.TextChoices): ...


class AgentConfigSerializer(PassiveSerializer):

    device_id = SerializerMethodField()
    refresh_interval = SerializerMethodField()

    authorization_flow = SerializerMethodField()
    jwks_auth = SerializerMethodField()
    jwks_challenge = SerializerMethodField()

    nss_uid_offset = IntegerField()
    nss_gid_offset = IntegerField()
    auth_terminate_session_on_expiry = BooleanField()

    system_config = SerializerMethodField()
    license_status = SerializerMethodField(required=False, allow_null=True)
    brand = SerializerMethodField(required=False, allow_null=True)

    def get_device_id(self, instance: AgentConnector) -> str:
        device: Device = self.context["device"]
        return device.pk

    def get_refresh_interval(self, instance: AgentConnector) -> int:
        return int(timedelta_from_string(instance.refresh_interval).total_seconds())

    def get_authorization_flow(self, instance: AgentConnector) -> str | None:
        if not instance.authorization_flow:
            return None
        return instance.authorization_flow.slug

    def get_jwks_auth(self, instance: AgentConnector) -> dict:
        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        return {"keys": [JWKSView.get_jwk_for_key(kp, "sig")]}

    def get_jwks_challenge(self, instance: AgentConnector) -> dict | None:
        if not instance.challenge_key:
            return None
        return {"keys": [JWKSView.get_jwk_for_key(instance.challenge_key, "sig")]}

    def get_system_config(self, instance: AgentConnector) -> ConfigSerializer:
        return ConfigView.get_config(self.context["request"]).data

    def get_license_status(self, instance: AgentConnector) -> LicenseUsageStatus:
        try:
            from authentik.enterprise.license import LicenseKey

            return LicenseKey.cached_summary().status
        except ModuleNotFoundError:
            return None

    def get_brand(self, instance: AgentConnector) -> CurrentBrandSerializer:
        brand: Brand = self.context["request"]._request.brand
        return CurrentBrandSerializer(brand, context=self.context).data


class EnrollSerializer(PassiveSerializer):

    device_serial = CharField(required=True)
    device_name = CharField(required=True)


class AgentTokenResponseSerializer(PassiveSerializer):

    token = CharField(required=True)
    expires_in = IntegerField(required=0)


class AgentAuthenticationResponse(PassiveSerializer):

    url = CharField()
