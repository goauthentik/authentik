from rest_framework.fields import (
    BooleanField,
    CharField,
    IntegerField,
    SerializerMethodField,
)

from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.lib.utils.time import timedelta_from_string


class AgentConfigSerializer(PassiveSerializer):

    domain_name = CharField()
    refresh_interval = SerializerMethodField()

    authorization_flow = CharField()

    nss_uid_offset = IntegerField()
    nss_gid_offset = IntegerField()
    auth_terminate_session_on_expiry = BooleanField()

    def get_refresh_interval(self, instance: AgentConnector) -> int:
        return int(timedelta_from_string(instance.refresh_interval).total_seconds())


class EnrollSerializer(PassiveSerializer):

    device_serial = CharField()
    device_name = CharField()


class EnrollResponseSerializer(PassiveSerializer):

    token = CharField()


class AgentAuthenticationRequest(PassiveSerializer): ...


class AgentAuthenticationResponse(PassiveSerializer):

    url = CharField()
