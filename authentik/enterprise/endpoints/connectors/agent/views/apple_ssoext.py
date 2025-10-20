from jwt import decode
from json import dumps, loads
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.http import HttpRequest, HttpResponseBadRequest
from django.views import View

from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.agent.stage import PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, QS_CHALLENGE_RESPONSE
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN


@method_decorator(xframe_options_sameorigin, name="dispatch")
class SSOExtensionView(View):

    def get(self, request: HttpRequest) -> HttpResponseBadRequest:
        plan = self.get_flow_plan()
        challenge = plan.context.get(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE)
        response = request.GET.get(QS_CHALLENGE_RESPONSE)
        raw = decode(
            response, options={"verify_signature": False}, issuer="goauthentik.io/platform/endpoint"
        )
        device = Device.objects.filter(identifier=raw["sub"])
        raw["atc"]

        return HttpResponseBadRequest()

    def get_flow_plan(self) -> FlowPlan:
        flow_plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        return flow_plan
