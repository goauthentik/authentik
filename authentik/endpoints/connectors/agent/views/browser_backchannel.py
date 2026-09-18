from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse
from rest_framework.exceptions import ValidationError

from authentik.endpoints.connectors.agent.controller import AgentController
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.endpoints.connectors.agent.stage import PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE
from authentik.endpoints.models import EndpointStage
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.views.frame import FlowFrameView


class BrowserBackchannel(FlowFrameView[EndpointStage]):

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        connector = AgentConnector.objects.filter(pk=self.stage.connector_id).first()
        if not connector:
            return HttpResponseBadRequest()
        self.controller: AgentController = connector.controller(connector)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        response = request.GET.get("xak-agent-response")
        with self.active_flow_plan() as plan:
            try:
                dev = self.controller.validate_device_challenge(
                    response, plan.context.get(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE)
                )
                plan.context[PLAN_CONTEXT_DEVICE] = dev
            except ValidationError:
                return HttpResponseBadRequest()
            return TemplateResponse(request, "flows/frame-submit.html")
