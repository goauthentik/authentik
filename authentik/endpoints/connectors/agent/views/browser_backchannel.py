from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse
from django.views import View
from rest_framework.exceptions import ValidationError

from authentik.endpoints.connectors.agent.controller import AgentController
from authentik.endpoints.connectors.agent.models import AgentConnector
from authentik.endpoints.connectors.agent.stage import PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE
from authentik.endpoints.models import EndpointStage
from authentik.flows.planner import PLAN_CONTEXT_DEVICE, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN


class BrowserBackchannel(View):
    def get_flow_plan(self) -> FlowPlan:
        flow_plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        return flow_plan

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        stage: EndpointStage = self.get_flow_plan().bindings[0].stage
        connector = AgentConnector.objects.filter(pk=stage.connector_id).first()
        if not connector:
            return HttpResponseBadRequest()
        self.controller: AgentController = connector.controller(connector)

    def get(self, request: HttpRequest) -> HttpResponse:
        response = request.GET.get("xak-agent-response")
        flow_plan = self.get_flow_plan()
        try:
            dev = self.controller.validate_device_challenge(
                response, flow_plan.context.get(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE)
            )
            flow_plan.context[PLAN_CONTEXT_DEVICE] = dev
            request.session[SESSION_KEY_PLAN] = flow_plan
        except ValidationError:
            return HttpResponseBadRequest()
        return TemplateResponse(request, "flows/frame-submit.html")
