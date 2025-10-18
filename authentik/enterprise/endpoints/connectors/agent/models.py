from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import ExpiringModel, default_token_key
from authentik.endpoints.models import Connector
from authentik.flows.stage import StageView


class AgentConnector(Connector):

    tokens = models.ManyToManyField("EnrollmentToken")

    nss_uid_offset = models.PositiveIntegerField(default=1000)
    nss_gid_offset = models.PositiveIntegerField(default=1000)
    authentication_flow = models.ForeignKey(
        "authentik_flows.Flow", null=True, on_delete=models.SET_DEFAULT, default=None
    )

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.enterprise.endpoints.connectors.agent.api.connector import (
            AgentConnectorSerializer,
        )

        return AgentConnectorSerializer

    @property
    def stage(self) -> type[StageView] | None:
        from authentik.enterprise.endpoints.connectors.agent.stage import (
            AuthenticatorEndpointStageView,
        )

        return AuthenticatorEndpointStageView

    @property
    def component(self) -> str:
        return "ak-endpoints-connector-agent"


class EnrollmentToken(ExpiringModel):
    token_uuid = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    key = models.TextField(default=default_token_key)

    class Meta:
        verbose_name = _("Enrollment Token")
        verbose_name_plural = _("Enrollment Tokens")
        indexes = ExpiringModel.Meta.indexes + [
            models.Index(fields=["key"]),
        ]
        permissions = [
            ("view_token_key", _("View token's key")),
        ]
