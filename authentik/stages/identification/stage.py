"""Identification stage logic"""

from dataclasses import asdict
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from django.utils.translation import gettext as _
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework.fields import BooleanField, CharField, ChoiceField, DictField, ListField
from rest_framework.serializers import ValidationError
from sentry_sdk import start_span

from authentik.core.api.utils import JSONDictField, PassiveSerializer
from authentik.core.models import Application, Source, User
from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.agent.views.auth_interactive import (
    PLAN_CONTEXT_DEVICE_AUTH_TOKEN,
)
from authentik.events.middleware import audit_ignore
from authentik.events.utils import sanitize_item
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    RedirectChallenge,
)
from authentik.flows.models import FlowDesignation
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_DEVICE,
    PLAN_CONTEXT_PENDING_USER,
)
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER, ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_GET, SESSION_KEY_OVERRIDE_LOGIN_HINT
from authentik.lib.avatars import DEFAULT_AVATAR
from authentik.lib.utils.reflection import all_subclasses, class_to_path
from authentik.lib.utils.urls import reverse_with_qs
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.authenticator_validate.challenge import (
    get_webauthn_challenge_without_user,
    validate_challenge_webauthn,
)
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
from authentik.stages.captcha.stage import (
    PLAN_CONTEXT_CAPTCHA_PRIVATE_KEY,
    CaptchaChallenge,
    verify_captcha_token,
)
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.identification.signals import identification_failed
from authentik.stages.password.stage import (
    PLAN_CONTEXT_METHOD,
    PLAN_CONTEXT_METHOD_ARGS,
    authenticate,
)


class LoginChallengeMixin:
    """Base login challenge for Identification stage"""


def get_login_serializers():
    mapping = {
        RedirectChallenge().fields["component"].default: RedirectChallenge,
    }
    for cls in all_subclasses(LoginChallengeMixin):
        mapping[cls().fields["component"].default] = cls
    return mapping


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="LoginChallengeTypes",
        serializers=get_login_serializers,
        resource_type_field_name="component",
    )
)
class ChallengeDictWrapper(DictField):
    """Wrapper around DictField that annotates itself as challenge proxy"""


class LoginSourceSerializer(PassiveSerializer):
    """Serializer for Login buttons of sources"""

    name = CharField()
    icon_url = CharField(required=False, allow_null=True)
    promoted = BooleanField(default=False)

    challenge = ChallengeDictWrapper()


class IdentificationChallenge(Challenge):
    """Identification challenges with all UI elements"""

    user_fields = ListField(child=CharField(), allow_empty=True, allow_null=True)
    password_fields = BooleanField()
    allow_show_password = BooleanField(default=False)
    application_pre = CharField(required=False)
    flow_designation = ChoiceField(FlowDesignation.choices)
    captcha_stage = CaptchaChallenge(required=False, allow_null=True)

    enroll_url = CharField(required=False)
    recovery_url = CharField(required=False)
    passwordless_url = CharField(required=False)
    primary_action = CharField()
    sources = LoginSourceSerializer(many=True, required=False)
    show_source_labels = BooleanField()
    enable_remember_me = BooleanField(required=False, default=True)

    passkey_challenge = JSONDictField(required=False, allow_null=True)

    component = CharField(default="ak-stage-identification")

    pending_user_identifier = CharField(required=False, allow_null=True)


class IdentificationChallengeResponse(ChallengeResponse):
    """Identification challenge"""

    uid_field = CharField(required=False, allow_blank=True, allow_null=True)
    password = CharField(required=False, allow_blank=True, allow_null=True)
    captcha_token = CharField(required=False, allow_blank=True, allow_null=True)
    passkey = JSONDictField(required=False, allow_null=True)
    component = CharField(default="ak-stage-identification")

    pre_user: User | None = None
    passkey_device: WebAuthnDevice | None = None

    def _validate_passkey_response(self, passkey: dict) -> WebAuthnDevice:
        """Validate passkey/WebAuthn response for passwordless authentication"""
        # Get the webauthn_stage from the current IdentificationStage
        current_stage: IdentificationStage = IdentificationStage.objects.get(
            pk=self.stage.executor.current_stage.pk
        )
        return validate_challenge_webauthn(
            passkey, self.stage, self.stage.get_pending_user(), current_stage.webauthn_stage
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate that user exists, and optionally their password, captcha token, or passkey"""
        current_stage: IdentificationStage = self.stage.executor.current_stage
        client_ip = ClientIPMiddleware.get_client_ip(self.stage.request)

        # Check if this is a passkey authentication
        passkey = attrs.get("passkey")
        if passkey:
            device = self._validate_passkey_response(passkey)
            self.passkey_device = device
            self.pre_user = device.user
            # Set backend so password stage policy knows user is already authenticated
            self.pre_user.backend = class_to_path(IdentificationStageView)
            return attrs

        # Standard username/password flow
        uid_field = attrs.get("uid_field")
        if not uid_field:
            raise ValidationError(_("No identification data provided."))

        pre_user = self.stage.get_user(uid_field)
        if not pre_user:
            with start_span(
                op="authentik.stages.identification.validate_invalid_wait",
                name="Sleep random time on invalid user identifier",
            ):
                # hash a random password on invalid identifier, same as with a valid identifier
                make_password(make_password(None))
            # Log in a similar format to Event.new(), but we don't want to create an event here
            # as this stage is mostly used by unauthenticated users with very high rate limits
            self.stage.logger.info(
                "invalid_login",
                identifier=uid_field,
                client_ip=client_ip,
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
            # when `pretend` is enabled, continue regardless
            if current_stage.pretend_user_exists and not current_stage.password_stage:
                return attrs
            raise ValidationError(_("Failed to authenticate."))
        self.pre_user = pre_user

        # Captcha check
        if captcha_stage := current_stage.captcha_stage:
            captcha_token = attrs.get("captcha_token", None)
            if not captcha_token:
                self.stage.logger.warning("Token not set for captcha attempt")
            try:
                verify_captcha_token(
                    captcha_stage,
                    captcha_token,
                    client_ip,
                    key=self.stage.executor.plan.context.get(PLAN_CONTEXT_CAPTCHA_PRIVATE_KEY),
                )
            except ValidationError:
                raise ValidationError(_("Failed to authenticate.")) from None

        # Password check
        if not current_stage.password_stage:
            # No password stage select, don't validate the password
            return attrs

        password = attrs.get("password", None)
        if not password:
            self.stage.logger.warning("Password not set for ident+auth attempt")
        try:
            with start_span(
                op="authentik.stages.identification.authenticate",
                name="User authenticate call (combo stage)",
            ):
                user = authenticate(
                    self.stage.request,
                    current_stage.password_stage.backends,
                    current_stage,
                    username=self.pre_user.username,
                    password=password,
                )
            if not user:
                raise ValidationError(_("Failed to authenticate."))
            self.pre_user = user
        except PermissionDenied as exc:
            raise ValidationError(str(exc)) from exc
        return attrs


class IdentificationStageView(ChallengeStageView):
    """Form to identify the user"""

    response_class = IdentificationChallengeResponse

    _override_login_hint: bool = False

    def get_user(self, uid_value: str) -> User | None:
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

    def get_passkey_challenge(self) -> dict | None:
        """Generate a WebAuthn challenge for passkey/conditional UI authentication"""
        # Refresh from DB to get the latest configuration
        current_stage: IdentificationStage = IdentificationStage.objects.get(
            pk=self.executor.current_stage.pk
        )
        if not current_stage.webauthn_stage:
            self.logger.debug("No webauthn_stage configured")
            return None
        challenge = get_webauthn_challenge_without_user(self, current_stage.webauthn_stage)
        self.logger.debug("Generated passkey challenge", challenge=challenge)
        return challenge

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check for login_hint and skip stage if found"""
        current_stage: IdentificationStage = self.executor.current_stage
        get_qs = self.request.session.get(SESSION_KEY_GET, self.request.GET)
        login_hint = get_qs.get("login_hint")

        # No login_hint, show challenge normally
        if not login_hint:
            return super().get(request, *args, **kwargs)

        # Prevent skip loop if user clicks "Not you?"
        if self.request.session.pop(SESSION_KEY_OVERRIDE_LOGIN_HINT, False):
            self._override_login_hint = True
            return super().get(request, *args, **kwargs)

        # Only skip if this is a "simple" identification stage with no extra features
        can_skip = (
            not current_stage.password_stage
            and not current_stage.captcha_stage
            and not current_stage.webauthn_stage
            and not self.executor.current_binding.policies.exists()
        )

        if can_skip:
            user = self.get_user(login_hint)
            if user:
                self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
            else:
                # Set dummy user
                self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = User(
                    username=login_hint,
                    email=login_hint,
                )
            return self.executor.stage_ok()

        # Can't skip - just pre-fill the username field
        return super().get(request, *args, **kwargs)

    def get_challenge(self) -> Challenge:
        current_stage: IdentificationStage = self.executor.current_stage
        challenge = IdentificationChallenge(
            data={
                "component": "ak-stage-identification",
                "primary_action": self.get_primary_action(),
                "user_fields": current_stage.user_fields,
                "password_fields": bool(current_stage.password_stage),
                "captcha_stage": (
                    {
                        "js_url": current_stage.captcha_stage.js_url,
                        "site_key": current_stage.captcha_stage.public_key,
                        "interactive": current_stage.captcha_stage.interactive,
                        "pending_user": "",
                        "pending_user_avatar": DEFAULT_AVATAR,
                    }
                    if current_stage.captcha_stage
                    else None
                ),
                "allow_show_password": bool(current_stage.password_stage)
                and current_stage.password_stage.allow_show_password,
                "show_source_labels": current_stage.show_source_labels,
                "flow_designation": self.executor.flow.designation,
                "enable_remember_me": current_stage.enable_remember_me,
                "passkey_challenge": self.get_passkey_challenge(),
            }
        )
        # If the user has been redirected to us whilst trying to access an
        # application, PLAN_CONTEXT_APPLICATION is set in the flow plan
        if PLAN_CONTEXT_APPLICATION in self.executor.plan.context:
            challenge.initial_data["application_pre"] = self.executor.plan.context.get(
                PLAN_CONTEXT_APPLICATION, Application()
            ).name
        if (
            PLAN_CONTEXT_DEVICE in self.executor.plan.context
            and PLAN_CONTEXT_DEVICE_AUTH_TOKEN in self.executor.plan.context
        ):
            challenge.initial_data["application_pre"] = self.executor.plan.context.get(
                PLAN_CONTEXT_DEVICE, Device()
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
                source_challenge = ui_login_button.challenge
                source_challenge.is_valid()
                button["challenge"] = source_challenge.data
                ui_sources.append(button)
        challenge.initial_data["sources"] = ui_sources

        # Pre-fill username from login_hint unless user clicked "Not you?"
        if not self._override_login_hint:
            if login_hint := get_qs.get("login_hint"):
                challenge.initial_data["pending_user_identifier"] = login_hint

        return challenge

    def challenge_valid(self, response: IdentificationChallengeResponse) -> HttpResponse:
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = response.pre_user
        current_stage: IdentificationStage = self.executor.current_stage

        # Handle passkey authentication
        if response.passkey_device:
            self.logger.debug("Passkey authentication successful", user=response.pre_user)
            self.executor.plan.context[PLAN_CONTEXT_METHOD] = "auth_webauthn_pwl"
            self.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
            self.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS].update(
                {
                    "device": response.passkey_device,
                    "device_type": response.passkey_device.device_type,
                }
            )
            # Update device last_used
            with audit_ignore():
                response.passkey_device.last_used = now()
                response.passkey_device.save()
            return self.executor.stage_ok()

        if not current_stage.show_matched_user:
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = (
                response.validated_data.get("uid_field")
            )
        return self.executor.stage_ok()
