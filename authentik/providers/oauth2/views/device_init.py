"""Device flow views"""
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.translation import gettext as _
from django.views import View
from rest_framework.exceptions import ErrorDetail
from rest_framework.fields import CharField, IntegerField
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.stage import ChallengeStageView
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.providers.oauth2.models import DeviceToken, OAuth2Provider
from authentik.providers.oauth2.views.userinfo import UserInfoView
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
)
from authentik.tenants.models import Tenant

LOGGER = get_logger()
PLAN_CONTEXT_DEVICE = "device"


class DeviceEntryView(View):
    """View used to initiate the device-code flow, url entered by endusers"""

    def dispatch(self, request: HttpRequest) -> HttpResponse:
        tenant: Tenant = request.tenant
        device_flow = tenant.flow_device_code
        if not device_flow:
            LOGGER.info("Tenant has no device code flow configured", tenant=tenant)
            raise Http404
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(device_flow)
        planner.allow_empty_flows = True
        plan = planner.plan(self.request)
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

    def get_application(self, provider: OAuth2Provider) -> Application:
        """Get application from provider"""
        try:
            app = provider.application
            if not app:
                raise Http404
            return app
        except Application.DoesNotExist:
            raise Http404

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        code = response.validated_data["code"]
        token = DeviceToken.objects.filter(
            user_code=code,
        ).first()
        if not token:
            response._errors.setdefault("code", [])
            response._errors["code"].append(ErrorDetail(_("Invalid code"), "invalid"))
            return self.challenge_invalid(response)

        app = self.get_application(token.provider)

        scope_descriptions = UserInfoView().get_scope_descriptions(token.scope)
        planner = FlowPlanner(token.provider.authorization_flow)
        planner.allow_empty_flows = True
        plan = planner.plan(
            self.request,
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
        # Run cancel to cleanup the current flow
        self.executor.cancel()
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=token.provider.authorization_flow.slug,
        )
