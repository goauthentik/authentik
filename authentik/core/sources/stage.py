"""Source flow manager stages"""

from django.db.utils import IntegrityError
from django.http import HttpRequest, HttpResponse

from authentik.core.models import User, UserSourceConnection
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
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

        try:
            connection.save()
        except IntegrityError:
            # If we hit a unique constraint violation, it means a connection already exists
            # for this user and source. Find the existing connection and use that instead.
            existing_connection = UserSourceConnection.objects.filter(
                user=user, source=connection.source
            ).first()
            if existing_connection:
                # We found an existing connection, so we'll update its identifier
                # if needed
                if existing_connection.identifier != connection.identifier:
                    existing_connection.identifier = connection.identifier
                    existing_connection.save()
                # Use the existing connection instead
                linked = False
            else:
                # If for some reason we can't find the existing connection, re-raise the error
                raise

        if linked:
            Event.new(
                EventAction.SOURCE_LINKED,
                message="Linked Source",
                source=connection.source,
            ).from_http(self.request)
        return self.executor.stage_ok()
