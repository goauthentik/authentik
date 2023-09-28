"""Identification stage logic"""
from dataclasses import asdict
from random import SystemRandom
from time import sleep
from typing import Any, Optional

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext as _
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework.fields import BooleanField, CharField, DictField, ListField
from rest_framework.serializers import ValidationError
from sentry_sdk.hub import Hub

from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Application, Source, User
from authentik.events.utils import sanitize_item
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    RedirectChallenge,
)
from authentik.flows.models import FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER, ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_APPLICATION_PRE, SESSION_KEY_GET
from authentik.lib.utils.http import get_client_ip
from authentik.lib.utils.urls import reverse_with_qs
from authentik.sources.oauth.types.apple import AppleLoginChallenge
from authentik.sources.plex.models import PlexAuthenticationChallenge
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.identification.signals import identification_failed
from authentik.stages.password.stage import authenticate


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="LoginChallengeTypes",
        serializers={
            RedirectChallenge().fields["component"].default: RedirectChallenge,
            PlexAuthenticationChallenge().fields["component"].default: PlexAuthenticationChallenge,
            AppleLoginChallenge().fields["component"].default: AppleLoginChallenge,
        },
        resource_type_field_name="component",
    )
)
class ChallengeDictWrapper(DictField):
    """Wrapper around DictField that annotates itself as challenge proxy"""


class LoginSourceSerializer(PassiveSerializer):
    """Serializer for Login buttons of sources"""

    name = CharField()
    icon_url = CharField(required=False, allow_null=True)

    challenge = ChallengeDictWrapper()


class IdentificationChallenge(Challenge):
    """Identification challenges with all UI elements"""

    user_fields = ListField(child=CharField(), allow_empty=True, allow_null=True)
    password_fields = BooleanField()
    application_pre = CharField(required=False)

    enroll_url = CharField(required=False)
    recovery_url = CharField(required=False)
    passwordless_url = CharField(required=False)
    primary_action = CharField()
    sources = LoginSourceSerializer(many=True, required=False)
    show_source_labels = BooleanField()

    component = CharField(default="ak-stage-identification")


class IdentificationChallengeResponse(ChallengeResponse):
    """Identification challenge"""

    uid_field = CharField()
    password = CharField(required=False, allow_blank=True, allow_null=True)
    component = CharField(default="ak-stage-identification")

    pre_user: Optional[User] = None

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that user exists, and optionally their password"""
        uid_field = attrs["uid_field"]
        current_stage: IdentificationStage = self.stage.executor.current_stage

        pre_user = self.stage.get_user(uid_field)
        if not pre_user:
            with Hub.current.start_span(
                op="authentik.stages.identification.validate_invalid_wait",
                description="Sleep random time on invalid user identifier",
            ):
                # Sleep a random time (between 90 and 210ms) to "prevent" user enumeration attacks
                sleep(0.030 * SystemRandom().randint(3, 7))
            # Log in a similar format to Event.new(), but we don't want to create an event here
            # as this stage is mostly used by unauthenticated users with very high rate limits
            self.stage.logger.info(
                "invalid_login",
                identifier=uid_field,
                client_ip=get_client_ip(self.stage.request),
                action="invalid_identifier",
                context={
                    "stage": sanitize_item(self.stage),
                },
            )
            identification_failed.send(sender=self, request=self.stage.request, uid_field=uid_field)
            # We set the pending_user even on failure so it's part of the context, even
            # when the input is invalid
            # This is so its part of the current flow plan, and on flow restart can be kept, and
            # policies can be applied.
            self.stage.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = User(
                username=uid_field,
                email=uid_field,
            )
            self.pre_user = self.stage.executor.plan.context[PLAN_CONTEXT_PENDING_USER]
            if not current_stage.show_matched_user:
                self.stage.executor.plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = uid_field
            if self.stage.executor.flow.designation == FlowDesignation.RECOVERY:
                # When used in a recovery flow, always continue to not disclose if a user exists
                return attrs
            raise ValidationError("Failed to authenticate.")
        self.pre_user = pre_user
        if not current_stage.password_stage:
            # No password stage select, don't validate the password
            return attrs

        password = attrs.get("password", None)
        if not password:
            self.stage.logger.warning("Password not set for ident+auth attempt")
        try:
            with Hub.current.start_span(
                op="authentik.stages.identification.authenticate",
                description="User authenticate call (combo stage)",
            ):
                user = authenticate(
                    self.stage.request,
                    current_stage.password_stage.backends,
                    current_stage,
                    username=self.pre_user.username,
                    password=password,
                )
            if not user:
                raise ValidationError("Failed to authenticate.")
            self.pre_user = user
        except PermissionDenied as exc:
            raise ValidationError(str(exc)) from exc
        return attrs


class IdentificationStageView(ChallengeStageView):
    """Form to identify the user"""

    response_class = IdentificationChallengeResponse

    def get_user(self, uid_value: str) -> Optional[User]:
        """Find user instance. Returns None if no user was found."""
        current_stage: IdentificationStage = self.executor.current_stage
        query = Q()
        for search_field in current_stage.user_fields:
            model_field = {
                "email": "email",
                "username": "username",
                "upn": "attributes__upn",
            }[search_field]
            if current_stage.case_insensitive_matching:
                model_field += "__iexact"
            else:
                model_field += "__exact"
            query |= Q(**{model_field: uid_value})
        if not query:
            self.logger.debug("Empty user query", query=query)
            return None
        user = User.objects.filter(query).first()
        if user:
            self.logger.debug("Found user", user=user.username, query=query)
            return user
        return None

    def get_primary_action(self) -> str:
        """Get the primary action label for this stage"""
        if self.executor.flow.designation == FlowDesignation.AUTHENTICATION:
            return _("Log in")
        return _("Continue")

    def get_challenge(self) -> Challenge:
        current_stage: IdentificationStage = self.executor.current_stage
        challenge = IdentificationChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "primary_action": self.get_primary_action(),
                "component": "ak-stage-identification",
                "user_fields": current_stage.user_fields,
                "password_fields": bool(current_stage.password_stage),
                "show_source_labels": current_stage.show_source_labels,
            }
        )
        # If the user has been redirected to us whilst trying to access an
        # application, SESSION_KEY_APPLICATION_PRE is set in the session
        if SESSION_KEY_APPLICATION_PRE in self.request.session:
            challenge.initial_data["application_pre"] = self.request.session.get(
                SESSION_KEY_APPLICATION_PRE, Application()
            ).name
        get_qs = self.request.session.get(SESSION_KEY_GET, self.request.GET)
        # Check for related enrollment and recovery flow, add URL to view
        if current_stage.enrollment_flow:
            challenge.initial_data["enroll_url"] = reverse_with_qs(
                "authentik_core:if-flow",
                query=get_qs,
                kwargs={"flow_slug": current_stage.enrollment_flow.slug},
            )
        if current_stage.recovery_flow:
            challenge.initial_data["recovery_url"] = reverse_with_qs(
                "authentik_core:if-flow",
                query=get_qs,
                kwargs={"flow_slug": current_stage.recovery_flow.slug},
            )
        if current_stage.passwordless_flow:
            challenge.initial_data["passwordless_url"] = reverse_with_qs(
                "authentik_core:if-flow",
                query=get_qs,
                kwargs={"flow_slug": current_stage.passwordless_flow.slug},
            )

        # Check all enabled source, add them if they have a UI Login button.
        ui_sources = []
        sources: list[Source] = (
            current_stage.sources.filter(enabled=True).order_by("name").select_subclasses()
        )
        for source in sources:
            ui_login_button = source.ui_login_button(self.request)
            if ui_login_button:
                button = asdict(ui_login_button)
                button["challenge"] = ui_login_button.challenge.data
                ui_sources.append(button)
        challenge.initial_data["sources"] = ui_sources
        return challenge

    def challenge_valid(self, response: IdentificationChallengeResponse) -> HttpResponse:
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = response.pre_user
        current_stage: IdentificationStage = self.executor.current_stage
        if not current_stage.show_matched_user:
            self.executor.plan.context[
                PLAN_CONTEXT_PENDING_USER_IDENTIFIER
            ] = response.validated_data.get("uid_field")
        return self.executor.stage_ok()
