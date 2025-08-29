"""Source decision helper"""

from typing import Any

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import (
    Group,
    GroupSourceConnection,
    Source,
    User,
    UserSourceConnection,
)
from authentik.core.sources.mapper import SourceMapper
from authentik.core.sources.matcher import Action, SourceMatcher
from authentik.core.sources.stage import (
    PLAN_CONTEXT_SOURCES_CONNECTION,
    PostSourceStage,
)
from authentik.events.models import Event, EventAction
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import Flow, FlowToken, Stage, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_IS_RESTORED,
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.stage import StageView
from authentik.flows.views.executor import NEXT_ARG_NAME, SESSION_KEY_GET
from authentik.lib.views import bad_request_message
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.utils import delete_none_values
from authentik.stages.password import BACKEND_INBUILT
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.stage import PLAN_CONTEXT_USER_PATH

LOGGER = get_logger()

PLAN_CONTEXT_SOURCE_GROUPS = "source_groups"
SESSION_KEY_SOURCE_FLOW_STAGES = "authentik/flows/source_flow_stages"
SESSION_KEY_SOURCE_FLOW_CONTEXT = "authentik/flows/source_flow_context"
SESSION_KEY_OVERRIDE_FLOW_TOKEN = "authentik/flows/source_override_flow_token"  # nosec


class MessageStage(StageView):
    """Show a pre-configured message after the flow is done"""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Show a pre-configured message after the flow is done"""
        message = getattr(self.executor.current_stage, "message", "")
        level = getattr(self.executor.current_stage, "level", messages.SUCCESS)
        messages.add_message(
            self.request,
            level,
            message,
        )
        return self.executor.stage_ok()


class SourceFlowManager:
    """Help sources decide what they should do after authorization. Based on source settings and
    previous connections, authenticate the user, enroll a new user, link to an existing user
    or deny the request."""

    source: Source
    mapper: SourceMapper
    matcher: SourceMatcher
    request: HttpRequest

    identifier: str

    user_connection_type: type[UserSourceConnection]
    group_connection_type: type[GroupSourceConnection]

    user_info: dict[str, Any]
    policy_context: dict[str, Any]
    user_properties: dict[str, Any | dict[str, Any]]
    groups_properties: dict[str, dict[str, Any | dict[str, Any]]]

    def __init__(
        self,
        source: Source,
        request: HttpRequest,
        identifier: str,
        user_info: dict[str, Any],
        policy_context: dict[str, Any],
    ) -> None:
        self.source = source
        self.mapper = SourceMapper(self.source)
        self.matcher = SourceMatcher(
            self.source, self.user_connection_type, self.group_connection_type
        )
        self.request = request
        self.identifier = identifier
        self.user_info = user_info
        self._logger = get_logger().bind(source=source, identifier=identifier)
        self.policy_context = policy_context

        self.user_properties = self.mapper.build_object_properties(
            object_type=User, request=request, user=None, **self.user_info
        )
        self.groups_properties = {
            group_id: self.mapper.build_object_properties(
                object_type=Group,
                request=request,
                user=None,
                group_id=group_id,
                **self.user_info,
            )
            for group_id in self.user_properties.setdefault("groups", [])
        }
        del self.user_properties["groups"]

    def get_action(self, **kwargs) -> tuple[Action, UserSourceConnection | None]:  # noqa: PLR0911
        """decide which action should be taken"""
        # When request is authenticated, always link
        if self.request.user.is_authenticated:
            new_connection = self.user_connection_type(
                source=self.source, identifier=self.identifier
            )
            new_connection.user = self.request.user
            new_connection = self.update_user_connection(new_connection, **kwargs)
            if existing := self.user_connection_type.objects.filter(
                source=self.source, identifier=self.identifier
            ).first():
                existing = self.update_user_connection(existing)
                return Action.AUTH, existing
            return Action.LINK, new_connection

        action, connection = self.matcher.get_user_action(self.identifier, self.user_properties)
        if connection:
            connection = self.update_user_connection(connection, **kwargs)
        return action, connection

    def update_user_connection(
        self, connection: UserSourceConnection, **kwargs
    ) -> UserSourceConnection:  # pragma: no cover
        """Optionally make changes to the user connection after it is looked up/created."""
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
                "Request to authenticate with {source} has been denied. Please authenticate "
                "with the source you've previously signed up with.".format_map(
                    {"source": self.source.name}
                )
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
        return [
            in_memory_stage(PostSourceStage),
        ]

    def _prepare_flow(
        self,
        flow: Flow | None,
        connection: UserSourceConnection,
        stages: list[StageView] | None = None,
        **flow_context,
    ) -> HttpResponse:
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        # Ensure redirect is carried through when user was trying to
        # authorize application
        final_redirect = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, "authentik_core:if-user"
        )
        flow_context.update(
            {
                # Since we authenticate the user by their token, they have no backend set
                PLAN_CONTEXT_AUTHENTICATION_BACKEND: BACKEND_INBUILT,
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_SOURCE: self.source,
                PLAN_CONTEXT_SOURCES_CONNECTION: connection,
                PLAN_CONTEXT_SOURCE_GROUPS: self.groups_properties,
            }
        )
        flow_context.update(self.policy_context)
        flow_context.setdefault(PLAN_CONTEXT_REDIRECT, final_redirect)

        if not flow:
            # We only check for the flow token here if we don't have a flow, otherwise we rely on
            # SESSION_KEY_SOURCE_FLOW_STAGES to delegate the usage of this token and dynamically add
            # stages that deal with this token to return to another flow
            if SESSION_KEY_OVERRIDE_FLOW_TOKEN in self.request.session:
                token: FlowToken = self.request.session.get(SESSION_KEY_OVERRIDE_FLOW_TOKEN)
                self._logger.info(
                    "Replacing source flow with overridden flow", flow=token.flow.slug
                )
                plan = token.plan
                plan.context[PLAN_CONTEXT_IS_RESTORED] = token
                plan.context.update(flow_context)
                for stage in self.get_stages_to_append(flow):
                    plan.append_stage(stage)
                if stages:
                    for stage in stages:
                        plan.append_stage(stage)
                redirect = plan.to_redirect(self.request, token.flow)
                token.delete()
                return redirect
            return bad_request_message(
                self.request,
                _("Configured flow does not exist."),
            )
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(flow)
        # We append some stages so the initial flow we get might be empty
        planner.allow_empty_flows = True
        planner.use_cache = False
        plan = planner.plan(self.request, flow_context)
        for stage in self.get_stages_to_append(flow):
            plan.append_stage(stage)
        plan.append_stage(
            in_memory_stage(GroupUpdateStage, group_connection_type=self.group_connection_type)
        )
        if stages:
            for stage in stages:
                plan.append_stage(stage)
        for stage in self.request.session.get(SESSION_KEY_SOURCE_FLOW_STAGES, []):
            plan.append_stage(stage)
        plan.context.update(self.request.session.get(SESSION_KEY_SOURCE_FLOW_CONTEXT, {}))
        return plan.to_redirect(self.request, flow)

    def handle_auth(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """Login user and redirect."""
        return self._prepare_flow(
            self.source.authentication_flow,
            connection,
            stages=[
                in_memory_stage(
                    MessageStage,
                    message=_(
                        "Successfully authenticated with {source}!".format_map(
                            {"source": self.source.name}
                        )
                    ),
                )
            ],
            **{
                PLAN_CONTEXT_PENDING_USER: connection.user,
                PLAN_CONTEXT_PROMPT: delete_none_values(self.user_properties),
                PLAN_CONTEXT_USER_PATH: self.source.get_user_path(),
            },
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
        # When an override flow token exists we actually still use a flow for link
        # to continue the existing flow we came from
        if SESSION_KEY_OVERRIDE_FLOW_TOKEN in self.request.session:
            return self._prepare_flow(None, connection)
        connection.save()
        Event.new(
            EventAction.SOURCE_LINKED,
            message="Linked Source",
            source=self.source,
        ).from_http(self.request)
        messages.success(
            self.request,
            _("Successfully linked {source}!".format_map({"source": self.source.name})),
        )
        return redirect(
            reverse(
                "authentik_core:if-user",
            )
            + "#/settings;page-sources"
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
                        "Successfully authenticated with {source}!".format_map(
                            {"source": self.source.name}
                        )
                    ),
                )
            ],
            **{
                PLAN_CONTEXT_PROMPT: delete_none_values(self.user_properties),
                PLAN_CONTEXT_USER_PATH: self.source.get_user_path(),
            },
        )


class GroupUpdateStage(StageView):
    """Dynamically injected stage which updates the user after enrollment/authentication."""

    def handle_group(
        self, group_id: str, group_properties: dict[str, Any | dict[str, Any]]
    ) -> Group | None:
        action, connection = self.matcher.get_group_action(group_id, group_properties)
        if action == Action.ENROLL:
            group = Group.objects.create(**group_properties)
            connection.group = group
            connection.save()
            return group
        elif action in (Action.LINK, Action.AUTH):
            group = connection.group
            group.update_attributes(group_properties)
            connection.save()
            return group

        return None

    def handle_groups(self) -> bool:
        self.source: Source = self.executor.plan.context[PLAN_CONTEXT_SOURCE]
        self.user: User = self.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
        self.group_connection_type: GroupSourceConnection = (
            self.executor.current_stage.group_connection_type
        )
        self.matcher = SourceMatcher(self.source, None, self.group_connection_type)

        raw_groups: dict[str, dict[str, Any | dict[str, Any]]] = self.executor.plan.context[
            PLAN_CONTEXT_SOURCE_GROUPS
        ]
        groups: list[Group] = []

        for group_id, group_properties in raw_groups.items():
            group = self.handle_group(group_id, group_properties)
            if not group:
                return False
            groups.append(group)

        with transaction.atomic():
            self.user.ak_groups.remove(
                *self.user.ak_groups.filter(groupsourceconnection__source=self.source)
            )
            self.user.ak_groups.add(*groups)

        return True

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Stage used after the user has been enrolled to sync their groups from source data"""
        if self.handle_groups():
            return self.executor.stage_ok()
        else:
            return self.executor.stage_invalid("Failed to update groups. Please try again later.")

    def post(self, request: HttpRequest) -> HttpResponse:
        """Wrapper for post requests"""
        return self.get(request)
