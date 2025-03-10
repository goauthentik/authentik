"""Device flow views"""

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from structlog.stdlib import get_logger

from authentik.brands.models import Brand
from authentik.core.models import Application
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.policies.views import PolicyAccessView
from authentik.providers.oauth2.models import DeviceToken
from authentik.providers.oauth2.views.device_finish import (
    PLAN_CONTEXT_DEVICE,
    OAuthDeviceCodeFinishStage,
)
from authentik.providers.oauth2.views.userinfo import UserInfoView
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)

LOGGER = get_logger()
QS_KEY_CODE = "code"  # nosec


class CodeValidatorView(PolicyAccessView):
    """Helper to validate frontside token"""

    def __init__(self, code: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.code = code

    def resolve_provider_application(self):
        self.token = DeviceToken.objects.filter(user_code=self.code).first()
        if not self.token:
            raise Application.DoesNotExist
        self.provider = self.token.provider
        self.application = self.token.provider.application

    def post(self, request: HttpRequest, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs):
        scope_descriptions = UserInfoView().get_scope_descriptions(self.token.scope, self.provider)
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        planner.use_cache = False
        try:
            plan = planner.plan(
                request,
                {
                    PLAN_CONTEXT_SSO: True,
                    PLAN_CONTEXT_APPLICATION: self.application,
                    # OAuth2 related params
                    PLAN_CONTEXT_DEVICE: self.token,
                    # Consent related params
                    PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                    % {"application": self.application.name},
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: scope_descriptions,
                },
            )
        except FlowNonApplicableException:
            LOGGER.warning("Flow not applicable to user")
            return None
        plan.append_stage(in_memory_stage(OAuthDeviceCodeFinishStage))
        return plan.to_redirect(self.request, self.token.provider.authorization_flow)


class DeviceEntryView(PolicyAccessView):
    """View used to initiate the device-code flow, url entered by endusers"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        brand: Brand = request.brand
        device_flow = brand.flow_device_code
        if not device_flow:
            LOGGER.info("Brand has no device code flow configured", brand=brand)
            return HttpResponse(status=404)
        if QS_KEY_CODE in request.GET:
            validation = CodeValidatorView(request.GET[QS_KEY_CODE], request=request).dispatch(
                request
            )
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
        return plan.to_redirect(self.request, device_flow)


class OAuthDeviceCodeChallenge(Challenge):
    """OAuth Device code challenge"""

    component = CharField(default="ak-provider-oauth2-device-code")


class OAuthDeviceCodeChallengeResponse(ChallengeResponse):
    """Response that includes the user-entered device code"""

    code = CharField()
    component = CharField(default="ak-provider-oauth2-device-code")

    def validate_code(self, code: int) -> HttpResponse | None:
        """Validate code and save the returned http response"""
        response = CodeValidatorView(code, request=self.stage.request).dispatch(self.stage.request)
        if not response:
            raise ValidationError(_("Invalid code"), "invalid")
        return response


class OAuthDeviceCodeStage(ChallengeStageView):
    """Flow challenge for users to enter device code"""

    response_class = OAuthDeviceCodeChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return OAuthDeviceCodeChallenge(
            data={
                "component": "ak-provider-oauth2-device-code",
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return response.validated_data["code"]
