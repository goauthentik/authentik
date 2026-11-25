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
from authentik.policies.types import PolicyRequest
from authentik.policies.views import PolicyAccessView
from authentik.providers.oauth2.client import OAuthClientContext, OAuthClientResolver
from authentik.providers.oauth2.models import DeviceToken
from authentik.providers.oauth2.views.authorize import (
    PLAN_CONTEXT_OAUTH_CLIENT,
    consent_client_for,
)
from authentik.providers.oauth2.views.device_finish import (
    PLAN_CONTEXT_DEVICE,
    OAuthDeviceCodeFinishStage,
)
from authentik.providers.oauth2.views.userinfo import UserInfoView
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_CLIENT,
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)

LOGGER = get_logger()
QS_KEY_CODE = "code"  # nosec


class CodeValidatorView(PolicyAccessView):
    """Helper to validate frontside token"""

    token: DeviceToken
    # Client the device code was issued to
    client: OAuthClientContext

    def __init__(self, code: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.code = code

    def get_client_resolver(self) -> OAuthClientResolver:
        """Resolver used to find the client the device code was issued to, within the
        device code's provider"""
        return OAuthClientResolver.legacy()

    def resolve_provider_application(self):
        token = DeviceToken.objects.select_related("provider").filter(user_code=self.code).first()
        if not token:
            raise Application.DoesNotExist
        client = self.get_client_resolver().resolve_in_provider(
            self.request, token.provider, token.bound_client_id
        )
        if not client or not token.is_bound_to(client):
            LOGGER.warning(
                "Client of device code could not be resolved", client_id=token.bound_client_id
            )
            raise Application.DoesNotExist
        self.token = token
        self.client = client
        self.provider = token.provider
        self.application = token.provider.application

    def modify_policy_request(self, request: PolicyRequest) -> PolicyRequest:
        request.context[PLAN_CONTEXT_OAUTH_CLIENT] = self.client
        return request

    def post(self, request: HttpRequest, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs):
        scope_descriptions = UserInfoView().get_scope_descriptions(self.token.scope, self.provider)
        authorization_flow = self.client.authorization_flow
        planner = FlowPlanner(authorization_flow)
        planner.allow_empty_flows = True
        planner.use_cache = False
        context: dict[str, Any] = {
            PLAN_CONTEXT_SSO: True,
            PLAN_CONTEXT_APPLICATION: self.application,
            # OAuth2 related params
            PLAN_CONTEXT_DEVICE: self.token,
            PLAN_CONTEXT_OAUTH_CLIENT: self.client,
            # Consent related params
            PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
            % {"application": self.application.name},
            PLAN_CONTEXT_CONSENT_PERMISSIONS: scope_descriptions,
        }
        # Consent for a device code is given to the client it was issued to, exactly like
        # consent in the authorization code flow
        consent_client = consent_client_for(self.client)
        if consent_client:
            context[PLAN_CONTEXT_CONSENT_CLIENT] = consent_client
        try:
            plan = planner.plan(request, context)
        except FlowNonApplicableException:
            LOGGER.warning("Flow not applicable to user")
            return None
        plan.append_stage(in_memory_stage(OAuthDeviceCodeFinishStage))
        return plan.to_redirect(self.request, authorization_flow)


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
