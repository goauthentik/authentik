from typing import Any

from django.http import HttpResponse
from jwt import PyJWTError, decode, encode
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.endpoints.models import Device
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
)
from authentik.flows.stage import ChallengeStageView
from authentik.lib.generators import generate_id

PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE = "goauthentik.io/endpoints/connectors/agent/challenge"
QS_CHALLENGE = "challenge"
QS_CHALLENGE_RESPONSE = "response"


class EndpointAgentChallenge(Challenge):

    component = CharField(default="ak-stage-endpoint-agent")
    challenge = CharField()


class EndpointAgentChallengeResponse(ChallengeResponse):

    component = CharField(default="ak-stage-endpoint-agent")
    response = CharField()

    def validate_response(self, response: str) -> dict[str, Any]:
        raw = decode(
            response, options={"verify_signature": False}, issuer="goauthentik.io/platform/endpoint"
        )
        device = Device.objects.filter(identifier=raw["sub"]).first()
        if not device:
            raise ValidationError("Device not found")
        try:
            return decode(
                response,
                key=device.token,
                issuer="goauthentik.io/platform/endpoint",
                audience=device,
            )
        except PyJWTError:
            raise ValidationError("Invalid challenge response") from None


class AuthenticatorEndpointStageView(ChallengeStageView):
    """Endpoint stage"""

    response_class = EndpointAgentChallengeResponse

    def validate_response(self, response: str):
        pass

    def get_challenge(self, *args, **kwargs) -> Challenge:
        challenge_str = generate_id()
        challenge = encode(
            {
                "atc": challenge_str,
                "iss": str(self.executor.current_stage.pk),
            },
            key=self.executor.current_stage.connector.challenge_key.private_key,
        )
        self.executor.plan.context[PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE] = challenge
        return EndpointAgentChallenge(
            data={
                "component": "ak-stage-endpoint-agent",
                "challenge": challenge,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
