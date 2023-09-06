"""Source flow manager stages"""
from django.http import HttpRequest, HttpResponse

from authentik.core.models import User, UserSourceConnection
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView

PLAN_CONTEXT_SOURCES_CONNECTION = "goauthentik.io/sources/connection"


class PostUserEnrollmentStage(StageView):
    """Dynamically injected stage which saves the Connection after
    the user has been enrolled."""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        """Stage used after the user has been enrolled"""
        connection: UserSourceConnection = self.executor.plan.context[
            PLAN_CONTEXT_SOURCES_CONNECTION
        ]
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        connection.user = user
        connection.save()
        Event.new(
            EventAction.SOURCE_LINKED,
            message="Linked Source",
            source=connection.source,
        ).from_http(self.request)
        return self.executor.stage_ok()
