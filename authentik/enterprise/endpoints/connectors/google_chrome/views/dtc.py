from typing import Any

from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from authentik.endpoints.models import EndpointStage
from authentik.enterprise.endpoints.connectors.google_chrome.controller import (
    HEADER_ACCESS_CHALLENGE_RESPONSE,
    HEADER_DEVICE_TRUST,
    GoogleChromeController,
)
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN


@method_decorator(xframe_options_sameorigin, name="dispatch")
class GoogleChromeDeviceTrustConnector(View):
    """Google Chrome Device-trust connector based endpoint authenticator"""

    def get_flow_plan(self) -> FlowPlan:
        flow_plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        return flow_plan

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        stage: EndpointStage = self.get_flow_plan().bindings[0].stage
        self.controller: GoogleChromeController = stage.connector.controller

    def get(self, request: HttpRequest) -> HttpResponse:
        x_device_trust = request.headers.get(HEADER_DEVICE_TRUST)
        x_access_challenge_response = request.headers.get(HEADER_ACCESS_CHALLENGE_RESPONSE)
        if x_device_trust == "VerifiedAccess" and x_access_challenge_response is None:
            return self.controller.generate_challenge()
        if x_access_challenge_response:
            self.controller.validate_challenge(x_access_challenge_response)
        return TemplateResponse(request, "endpoints/google_chrome/dtc.html")
