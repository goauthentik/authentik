from json import dumps, loads
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from googleapiclient.discovery import build

from authentik.enterprise.stages.authenticator_endpoint_gdtc.models import (
    AuthenticatorEndpointGDTCStage,
    EndpointDevice,
    EndpointDeviceConnection,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

# Header we get from chrome that initiates verified access
HEADER_DEVICE_TRUST = "X-Device-Trust"
# Header we send to the client with the challenge
HEADER_ACCESS_CHALLENGE = "X-Verified-Access-Challenge"
# Header we get back from the client that we verify with google
HEADER_ACCESS_CHALLENGE_RESPONSE = "X-Verified-Access-Challenge-Response"
# Header value for x-device-trust that initiates the flow
DEVICE_TRUST_VERIFIED_ACCESS = "VerifiedAccess"


@method_decorator(xframe_options_sameorigin, name="dispatch")
class GoogleChromeDeviceTrustConnector(View):
    """Google Chrome Device-trust connector based endpoint authenticator"""

    def get_flow_plan(self) -> FlowPlan:
        flow_plan: FlowPlan = self.request.session[SESSION_KEY_PLAN]
        return flow_plan

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        stage: AuthenticatorEndpointGDTCStage = self.get_flow_plan().bindings[0].stage
        self.google_client = build(
            "verifiedaccess",
            "v2",
            cache_discovery=False,
            **stage.google_credentials(),
        )

    def get(self, request: HttpRequest) -> HttpResponse:
        x_device_trust = request.headers.get(HEADER_DEVICE_TRUST)
        x_access_challenge_response = request.headers.get(HEADER_ACCESS_CHALLENGE_RESPONSE)
        if x_device_trust == "VerifiedAccess" and x_access_challenge_response is None:
            challenge = self.google_client.challenge().generate().execute()
            res = HttpResponseRedirect(
                self.request.build_absolute_uri(
                    reverse("authentik_stages_authenticator_endpoint_gdtc:chrome")
                )
            )
            res[HEADER_ACCESS_CHALLENGE] = dumps(challenge)
            return res
        if x_access_challenge_response:
            response = (
                self.google_client.challenge()
                .verify(body=loads(x_access_challenge_response))
                .execute()
            )
            # Remove deprecated string representation of deviceSignals
            response.pop("deviceSignal", None)
            flow_plan: FlowPlan = self.get_flow_plan()
            device, _ = EndpointDevice.objects.update_or_create(
                host_identifier=response["deviceSignals"]["serialNumber"],
                user=flow_plan.context.get(PLAN_CONTEXT_PENDING_USER),
                defaults={"name": response["deviceSignals"]["hostname"], "data": response},
            )
            EndpointDeviceConnection.objects.update_or_create(
                device=device,
                stage=flow_plan.bindings[0].stage,
                defaults={
                    "attributes": response,
                },
            )
            flow_plan.context.setdefault(PLAN_CONTEXT_METHOD, "trusted_endpoint")
            flow_plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
            flow_plan.context[PLAN_CONTEXT_METHOD_ARGS].setdefault("endpoints", [])
            flow_plan.context[PLAN_CONTEXT_METHOD_ARGS]["endpoints"].append(response)
            request.session[SESSION_KEY_PLAN] = flow_plan
        return TemplateResponse(request, "stages/authenticator_endpoint/google_chrome_dtc.html")
