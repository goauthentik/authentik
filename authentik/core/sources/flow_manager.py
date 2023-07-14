"""Source decision helper"""
from enum import Enum
from typing import Any, Optional

from django.contrib import messages
from django.db import IntegrityError
from django.db.models.query_utils import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import Source, SourceUserMatchingModes, User, UserSourceConnection
from authentik.core.sources.stage import PLAN_CONTEXT_SOURCES_CONNECTION, PostUserEnrollmentStage
from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, Stage, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.stage import StageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.lib.views import bad_request_message
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.utils import delete_none_values
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.stage import PLAN_CONTEXT_USER_PATH


class Action(Enum):
    """Actions that can be decided based on the request
    and source settings"""

    LINK = "link"
    AUTH = "auth"
    ENROLL = "enroll"
    DENY = "deny"


class MessageStage(StageView):
    """Show a pre-configured message after the flow is done"""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Show a pre-configured message after the flow is done"""
        message = getattr(self.executor.current_stage, "message", "")
        level = getattr(self.executor.current_stage, "level", messages.SUCCESS)
        messages.add_message(
            self.request,
            level,
            message,
        )
        return self.executor.stage_ok()

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)


class SourceFlowManager:
    """Help sources decide what they should do after authorization. Based on source settings and
    previous connections, authenticate the user, enroll a new user, link to an existing user
    or deny the request."""

    source: Source
    request: HttpRequest

    identifier: str

    connection_type: type[UserSourceConnection] = UserSourceConnection

    enroll_info: dict[str, Any]
    policy_context: dict[str, Any]

    def __init__(
        self,
        source: Source,
        request: HttpRequest,
        identifier: str,
        enroll_info: dict[str, Any],
    ) -> None:
        self.source = source
        self.request = request
        self.identifier = identifier
        self.enroll_info = enroll_info
        self._logger = get_logger().bind(source=source, identifier=identifier)
        self.policy_context = {}

    # pylint: disable=too-many-return-statements
    def get_action(self, **kwargs) -> tuple[Action, Optional[UserSourceConnection]]:
        """decide which action should be taken"""
        new_connection = self.connection_type(source=self.source, identifier=self.identifier)
        # When request is authenticated, always link
        if self.request.user.is_authenticated:
            new_connection.user = self.request.user
            new_connection = self.update_connection(new_connection, **kwargs)
            new_connection.save()
            return Action.LINK, new_connection

        existing_connections = self.connection_type.objects.filter(
            source=self.source, identifier=self.identifier
        )
        if existing_connections.exists():
            connection = existing_connections.first()
            return Action.AUTH, self.update_connection(connection, **kwargs)
        # No connection exists, but we match on identifier, so enroll
        if self.source.user_matching_mode == SourceUserMatchingModes.IDENTIFIER:
            # We don't save the connection here cause it doesn't have a user assigned yet
            return Action.ENROLL, self.update_connection(new_connection, **kwargs)

        # Check for existing users with matching attributes
        query = Q()
        # Either query existing user based on email or username
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_LINK,
            SourceUserMatchingModes.EMAIL_DENY,
        ]:
            if not self.enroll_info.get("email", None):
                self._logger.warning("Refusing to use none email", source=self.source)
                return Action.DENY, None
            query = Q(email__exact=self.enroll_info.get("email", None))
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.USERNAME_LINK,
            SourceUserMatchingModes.USERNAME_DENY,
        ]:
            if not self.enroll_info.get("username", None):
                self._logger.warning("Refusing to use none username", source=self.source)
                return Action.DENY, None
            query = Q(username__exact=self.enroll_info.get("username", None))
        self._logger.debug("trying to link with existing user", query=query)
        matching_users = User.objects.filter(query)
        # No matching users, always enroll
        if not matching_users.exists():
            self._logger.debug("no matching users found, enrolling")
            return Action.ENROLL, self.update_connection(new_connection, **kwargs)

        user = matching_users.first()
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_LINK,
            SourceUserMatchingModes.USERNAME_LINK,
        ]:
            new_connection.user = user
            new_connection = self.update_connection(new_connection, **kwargs)
            new_connection.save()
            return Action.LINK, new_connection
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_DENY,
            SourceUserMatchingModes.USERNAME_DENY,
        ]:
            self._logger.info("denying source because user exists", user=user)
            return Action.DENY, None
        # Should never get here as default enroll case is returned above.
        return Action.DENY, None  # pragma: no cover

    def update_connection(
        self, connection: UserSourceConnection, **kwargs
    ) -> UserSourceConnection:  # pragma: no cover
        """Optionally make changes to the connection after it is looked up/created."""
        return connection

    def get_flow(self, **kwargs) -> HttpResponse:
        """Get the flow response based on user_matching_mode"""
        try:
            action, connection = self.get_action(**kwargs)
        except IntegrityError as exc:
            self._logger.warning("failed to get action", exc=exc)
            return redirect(reverse("authentik_core:root-redirect"))
        self._logger.debug("get_action", action=action, connection=connection)
        try:
            if connection:
                if action == Action.LINK:
                    self._logger.debug("Linking existing user")
                    return self.handle_existing_link(connection)
                if action == Action.AUTH:
                    self._logger.debug("Handling auth user")
                    return self.handle_auth(connection)
                if action == Action.ENROLL:
                    self._logger.debug("Handling enrollment of new user")
                    return self.handle_enroll(connection)
        except FlowNonApplicableException as exc:
            self._logger.warning("Flow non applicable", exc=exc)
            return self.error_handler(exc)
        # Default case, assume deny
        error = Exception(
            _(
                "Request to authenticate with %(source)s has been denied. Please authenticate "
                "with the source you've previously signed up with." % {"source": self.source.name}
            ),
        )
        return self.error_handler(error)

    def error_handler(self, error: Exception) -> HttpResponse:
        """Handle any errors by returning an access denied stage"""
        response = AccessDeniedResponse(self.request)
        response.error_message = str(error)
        if isinstance(error, FlowNonApplicableException):
            response.policy_result = error.policy_result
            response.error_message = error.messages
        return response

    def get_stages_to_append(self, flow: Flow) -> list[Stage]:
        """Hook to override stages which are appended to the flow"""
        if not self.source.enrollment_flow:
            return []
        if flow.slug == self.source.enrollment_flow.slug:
            return [
                in_memory_stage(PostUserEnrollmentStage),
            ]
        return []

    def _prepare_flow(
        self,
        flow: Flow,
        connection: UserSourceConnection,
        stages: Optional[list[StageView]] = None,
        **kwargs,
    ) -> HttpResponse:
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        # Ensure redirect is carried through when user was trying to
        # authorize application
        final_redirect = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, "authentik_core:if-user"
        )
        kwargs.update(
            {
                # Since we authenticate the user by their token, they have no backend set
                PLAN_CONTEXT_AUTHENTICATION_BACKEND: BACKEND_INBUILT,
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_SOURCE: self.source,
                PLAN_CONTEXT_REDIRECT: final_redirect,
                PLAN_CONTEXT_SOURCES_CONNECTION: connection,
            }
        )
        kwargs.update(self.policy_context)
        if not flow:
            return bad_request_message(
                self.request,
                _("Configured flow does not exist."),
            )
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(flow)
        plan = planner.plan(self.request, kwargs)
        for stage in self.get_stages_to_append(flow):
            plan.append_stage(stage)
        if stages:
            for stage in stages:
                plan.append_stage(stage)
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=flow.slug,
        )

    def handle_auth(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """Login user and redirect."""
        flow_kwargs = {PLAN_CONTEXT_PENDING_USER: connection.user}
        return self._prepare_flow(
            self.source.authentication_flow,
            connection,
            stages=[
                in_memory_stage(
                    MessageStage,
                    message=_(
                        "Successfully authenticated with %(source)s!" % {"source": self.source.name}
                    ),
                )
            ],
            **flow_kwargs,
        )

    def handle_existing_link(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """Handler when the user was already authenticated and linked an external source
        to their account."""
        # When request isn't authenticated we jump straight to auth
        if not self.request.user.is_authenticated:
            return self.handle_auth(connection)
        # Connection has already been saved
        Event.new(
            EventAction.SOURCE_LINKED,
            message="Linked Source",
            source=self.source,
        ).from_http(self.request)
        messages.success(
            self.request,
            _("Successfully linked %(source)s!" % {"source": self.source.name}),
        )
        return redirect(
            reverse(
                "authentik_core:if-user",
            )
            + f"#/settings;page-{self.source.slug}"
        )

    def handle_enroll(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """User was not authenticated and previous request was not authenticated."""
        # We run the Flow planner here so we can pass the Pending user in the context
        if not self.source.enrollment_flow:
            self._logger.warning("source has no enrollment flow")
            return bad_request_message(
                self.request,
                _("Source is not configured for enrollment."),
            )
        return self._prepare_flow(
            self.source.enrollment_flow,
            connection,
            stages=[
                in_memory_stage(
                    MessageStage,
                    message=_(
                        "Successfully authenticated with %(source)s!" % {"source": self.source.name}
                    ),
                )
            ],
            **{
                PLAN_CONTEXT_PROMPT: delete_none_values(self.enroll_info),
                PLAN_CONTEXT_USER_PATH: self.source.get_user_path(),
            },
        )
