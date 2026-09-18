from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse

from authentik.endpoints.models import EndpointStage
from authentik.enterprise.endpoints.connectors.google_chrome.controller import (
    HEADER_ACCESS_CHALLENGE_RESPONSE,
    HEADER_DEVICE_TRUST,
    GoogleChromeController,
)
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.views.frame import FlowFrameView


class GoogleChromeDeviceTrustConnector(FlowFrameView[EndpointStage]):
    """Google Chrome Device-trust connector based endpoint authenticator"""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        connector = GoogleChromeConnector.objects.filter(pk=self.stage.connector_id).first()
        if not connector:
            return HttpResponseBadRequest()
        self.controller: GoogleChromeController = connector.controller(connector)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        x_device_trust = request.headers.get(HEADER_DEVICE_TRUST)
        x_access_challenge_response = request.headers.get(HEADER_ACCESS_CHALLENGE_RESPONSE)
        if x_device_trust == "VerifiedAccess" and x_access_challenge_response is None:
            return self.controller.generate_challenge(request)
        if x_access_challenge_response:
            device = self.controller.validate_challenge(x_access_challenge_response)
            with self.active_flow_plan() as plan:
                plan.context[PLAN_CONTEXT_DEVICE] = device
        return TemplateResponse(request, "flows/frame-submit.html")
