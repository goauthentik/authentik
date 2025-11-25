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
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.views.jwks import JWKSView


class AgentConfigSerializer(PassiveSerializer):

    domain_name = CharField()
    refresh_interval = SerializerMethodField()

    authorization_flow = CharField()
    jwks = SerializerMethodField()

    nss_uid_offset = IntegerField()
    nss_gid_offset = IntegerField()
    auth_terminate_session_on_expiry = BooleanField()

    system_config = SerializerMethodField()

    def get_jwks(self, instance: AgentConnector) -> dict:
        kp = CertificateKeyPair.objects.filter(managed=MANAGED_KEY).first()
        return {"keys": [JWKSView.get_jwk_for_key(kp, "sig")]}

    def get_refresh_interval(self, instance: AgentConnector) -> int:
        return int(timedelta_from_string(instance.refresh_interval).total_seconds())

    def get_system_config(self, instance: AgentConnector) -> ConfigSerializer:
        return ConfigView.get_config(self.context["request"]).data


class EnrollSerializer(PassiveSerializer):

    device_serial = CharField(required=True)
    device_name = CharField(required=True)


class AgentTokenResponseSerializer(PassiveSerializer):

    token = CharField(required=True)
    expires_in = IntegerField(required=0)


class AgentAuthenticationResponse(PassiveSerializer):

    url = CharField()
