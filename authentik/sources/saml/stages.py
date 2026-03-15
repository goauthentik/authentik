"""SAML Source stages and flow manager"""

from django.http import HttpRequest, HttpResponse
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession, User
from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.core.sources.stage import PostSourceStage
from authentik.flows.models import Flow, Stage, in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_SOURCE
from authentik.sources.saml.models import (
    GroupSAMLSourceConnection,
    SAMLSource,
    SAMLSourceSession,
    UserSAMLSourceConnection,
)

LOGGER = get_logger()

PLAN_CONTEXT_SAML_SESSION_DATA = "saml_session_data"


class SAMLPostSourceStage(PostSourceStage):
    """Extends PostSourceStage to also create SAMLSourceSession for SLO support."""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        response = super().dispatch(request)

        session_data = self.executor.plan.context.get(PLAN_CONTEXT_SAML_SESSION_DATA)
        if not session_data:
            return response

        source = self.executor.plan.context.get(PLAN_CONTEXT_SOURCE)
        if not isinstance(source, SAMLSource):
            return response

        user: User = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user or not user.pk:
            return response

        auth_session = AuthenticatedSession.from_request(request, user)
        if not auth_session:
            return response

        SAMLSourceSession.objects.create(
            source=source,
            user=user,
            session=auth_session,
            session_index=session_data.get("session_index", ""),
            name_id=session_data.get("name_id", ""),
            name_id_format=session_data.get("name_id_format", ""),
        )
        LOGGER.debug(
            "Created SAMLSourceSession",
            source=source.name,
            user=user,
            session_index=session_data.get("session_index", ""),
        )
        return response


class SAMLSourceFlowManager(SourceFlowManager):
    """Source flow manager for SAML Sources"""

    user_connection_type = UserSAMLSourceConnection
    group_connection_type = GroupSAMLSourceConnection

    def get_stages_to_append(self, flow: Flow) -> list[Stage]:
        return [
            in_memory_stage(SAMLPostSourceStage),
        ]
