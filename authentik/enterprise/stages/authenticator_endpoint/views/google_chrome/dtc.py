from json import dumps, loads
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views import View
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from authentik.enterprise.stages.authenticator_endpoint.models import (
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


class GoogleChromeDeviceTrustConnector(View):
    """Google Chrome Device-trust connector based endpoint authenticator"""

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.google_client = build(
            "verifiedaccess",
            "v2",
            cache_discovery=False,
            credentials=Credentials.from_service_account_file("sa.json"),
        )

    def get(self, request: HttpRequest) -> HttpResponse:
        x_device_trust = request.headers.get(HEADER_DEVICE_TRUST)
        x_access_challenge_response = request.headers.get(HEADER_ACCESS_CHALLENGE_RESPONSE)
        if x_device_trust == "VerifiedAccess" and x_access_challenge_response is None:
            challenge = self.google_client.challenge().generate().execute()
            res = HttpResponseRedirect(
                self.request.build_absolute_uri(
                    reverse("authentik_stages_authenticator_endpoint:chrome")
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
            flow_plan: FlowPlan = request.session[SESSION_KEY_PLAN]
            device, _ = EndpointDevice.objects.update_or_create(
                host_identifier=response["serialNumber"],
                user=flow_plan.context.get(PLAN_CONTEXT_PENDING_USER),
                defaults={"hostname": response["hostname"]},
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
