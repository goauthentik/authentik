"""Device flow views"""
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from django.views import View
from rest_framework.exceptions import ErrorDetail
from rest_framework.fields import CharField, IntegerField
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.providers.oauth2.models import DeviceToken, OAuth2Provider
from authentik.providers.oauth2.views.device_finish import (
    PLAN_CONTEXT_DEVICE,
    OAuthDeviceCodeFinishStage,
)
from authentik.providers.oauth2.views.userinfo import UserInfoView
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)
from authentik.tenants.models import Tenant

LOGGER = get_logger()
QS_KEY_CODE = "code"  # nosec


def get_application(provider: OAuth2Provider) -> Optional[Application]:
    """Get application from provider"""
    try:
        app = provider.application
        if not app:
            return None
        return app
    except Application.DoesNotExist:
        return None


def validate_code(code: int, request: HttpRequest) -> Optional[HttpResponse]:
    """Validate user token"""
    token = DeviceToken.objects.filter(
        user_code=code,
    ).first()
    if not token:
        return None

    app = get_application(token.provider)
    if not app:
        return None

    scope_descriptions = UserInfoView().get_scope_descriptions(token.scope, token.provider)
    planner = FlowPlanner(token.provider.authorization_flow)
    planner.allow_empty_flows = True
    try:
        plan = planner.plan(
            request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: app,
                # OAuth2 related params
                PLAN_CONTEXT_DEVICE: token,
                # Consent related params
                PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                % {"application": app.name},
                PLAN_CONTEXT_CONSENT_PERMISSIONS: scope_descriptions,
            },
        )
    except FlowNonApplicableException:
        LOGGER.warning("Flow not applicable to user")
        return None
    plan.insert_stage(in_memory_stage(OAuthDeviceCodeFinishStage))
    request.session[SESSION_KEY_PLAN] = plan
    return redirect_with_qs(
        "authentik_core:if-flow",
        request.GET,
        flow_slug=token.provider.authorization_flow.slug,
    )


class DeviceEntryView(View):
    """View used to initiate the device-code flow, url entered by endusers"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        tenant: Tenant = request.tenant
        device_flow = tenant.flow_device_code
        if not device_flow:
            LOGGER.info("Tenant has no device code flow configured", tenant=tenant)
            return HttpResponse(status=404)
        if QS_KEY_CODE in request.GET:
            validation = validate_code(request.GET[QS_KEY_CODE], request)
            if validation:
                return validation
            LOGGER.info("Got code from query parameter but no matching token found")

        # Regardless, we start the planner and return to it
        planner = FlowPlanner(device_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(self.request)
        except FlowNonApplicableException:
            LOGGER.warning("Flow not applicable to user")
            return HttpResponse(status=404)
        plan.append_stage(in_memory_stage(OAuthDeviceCodeStage))

        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=device_flow.slug,
        )


class OAuthDeviceCodeChallenge(Challenge):
    """OAuth Device code challenge"""

    component = CharField(default="ak-provider-oauth2-device-code")


class OAuthDeviceCodeChallengeResponse(ChallengeResponse):
    """Response that includes the user-entered device code"""

    code = IntegerField()
    component = CharField(default="ak-provider-oauth2-device-code")


class OAuthDeviceCodeStage(ChallengeStageView):
    """Flow challenge for users to enter device codes"""

    response_class = OAuthDeviceCodeChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return OAuthDeviceCodeChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "component": "ak-provider-oauth2-device-code",
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        code = response.validated_data["code"]
        validation = validate_code(code, self.request)
        if not validation:
            response._errors.setdefault("code", [])
            response._errors["code"].append(ErrorDetail(_("Invalid code"), "invalid"))
            return self.challenge_invalid(response)
        # Run cancel to cleanup the current flow
        self.executor.cancel()
        return validation
