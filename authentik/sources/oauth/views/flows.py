"""OAuth Stages"""
from django.http import HttpRequest, HttpResponse

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import StageView
from authentik.sources.oauth.models import UserOAuthSourceConnection

PLAN_CONTEXT_SOURCES_OAUTH_ACCESS = "sources_oauth_access"


class PostUserEnrollmentStage(StageView):
    """Dynamically injected stage which saves the OAuth Connection after
    the user has been enrolled."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        access: UserOAuthSourceConnection = self.executor.plan.context[
            PLAN_CONTEXT_SOURCES_OAUTH_ACCESS
        ]
        user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        access.user = user
        access.save()
        UserOAuthSourceConnection.objects.filter(pk=access.pk).update(user=user)
        Event.new(
            EventAction.SOURCE_LINKED,
            message="Linked OAuth Source",
            source=access.source,
        ).from_http(self.request)
        return self.executor.stage_ok()
