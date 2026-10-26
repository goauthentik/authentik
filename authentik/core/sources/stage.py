"""Source flow manager stages"""

from django.http import HttpRequest, HttpResponse

from authentik.core.models import User, UserSourceConnection
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowToken
from authentik.flows.planner import PLAN_CONTEXT_IS_RESTORED, PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView

PLAN_CONTEXT_SOURCES_CONNECTION = "goauthentik.io/sources/connection"


class PostSourceStage(StageView):
    """Dynamically injected stage which saves the Connection after
    the user has been enrolled."""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Stage used after the user has been enrolled"""
        connection: UserSourceConnection = self.executor.plan.context[
            PLAN_CONTEXT_SOURCES_CONNECTION
        ]
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        connection.user = user
        linked = connection.pk is None
        connection.save()
        if linked:
            Event.new(
                EventAction.SOURCE_LINKED,
                message="Linked Source",
                source=connection.source,
            ).from_http(self.request)
        return self.executor.stage_ok()


class ResumeParentFlowStage(StageView):
    """Resume a parent flow after authenticating through a source from identification."""

    def dispatch(self, *args, **kwargs):
        from authentik.core.sources.flow_manager import (
            PLAN_CONTEXT_SOURCE_MATCH_FAILURE_CONFIG,
            SESSION_KEY_OVERRIDE_FLOW_TOKEN,
            clear_source_flow_session,
        )

        token: FlowToken = self.request.session.get(SESSION_KEY_OVERRIDE_FLOW_TOKEN)
        if not token:
            clear_source_flow_session(self.request)
            return self.executor.stage_invalid("Flow token is invalid or expired")
        try:
            token.refresh_from_db()
        except FlowToken.DoesNotExist:
            clear_source_flow_session(self.request)
            return self.executor.stage_invalid("Flow token is invalid or expired")
        if token.is_expired:
            token.expire_action()
            clear_source_flow_session(self.request)
            return self.executor.stage_invalid("Flow token is invalid or expired")
        self.logger.info("Replacing source flow with overridden flow", flow=token.flow.slug)
        plan = token.plan
        plan.context.update(self.executor.plan.context)
        plan.context.pop(PLAN_CONTEXT_SOURCE_MATCH_FAILURE_CONFIG, None)
        plan.context[PLAN_CONTEXT_IS_RESTORED] = token
        response = plan.to_redirect(self.request, token.flow)
        token.delete()
        return response
