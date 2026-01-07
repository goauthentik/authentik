from rest_framework.fields import (
    BooleanField,
    CharField,
    IntegerField,
    SerializerMethodField,
)

from authentik.api.v3.config import ConfigSerializer, ConfigView
from authentik.core.api.utils import PassiveSerializer
from authentik.crypto.apps import MANAGED_KEY
from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.endpoints.models import Device
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.views.jwks import JWKSView

try:
    from authentik.enterprise.license import LicenseKey, LicenseSummarySerializer
except ImportError:
    class LicenseSummarySerializer(dict): ...
    class LicenseKey(dict): ...


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

    def get_license_status(self, instance: AgentConnector) -> "LicenseSummarySerializer":
        if not LicenseSummarySerializer:
            return None
        return LicenseSummarySerializer(instance=LicenseKey.cached_summary()).data


class EnrollSerializer(PassiveSerializer):

    device_serial = CharField(required=True)
    device_name = CharField(required=True)


class AgentTokenResponseSerializer(PassiveSerializer):

    token = CharField(required=True)
    expires_in = IntegerField(required=0)


class AgentAuthenticationResponse(PassiveSerializer):

    url = CharField()
