from hmac import compare_digest
from typing import Any

from django.http import HttpResponse
from jwt import PyJWTError, decode, encode
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField

from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import DeviceToken
from authentik.endpoints.models import Device, EndpointStage
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
)
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.stage import ChallengeStageView
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import JWTAlgorithms

PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE = "goauthentik.io/endpoints/connectors/agent/challenge"
QS_CHALLENGE = "challenge"
QS_CHALLENGE_RESPONSE = "response"


class EndpointAgentChallenge(Challenge):
    """Signed challenge for authentik agent to respond to"""

    component = CharField(default="ak-stage-endpoint-agent")
    challenge = CharField()


class EndpointAgentChallengeResponse(ChallengeResponse):
    """Response to signed challenge"""

    component = CharField(default="ak-stage-endpoint-agent")
    response = CharField()

    def validate_response(self, response: str) -> dict[str, Any]:
        raw = decode(
            response, options={"verify_signature": False}, issuer="goauthentik.io/platform/endpoint"
        )
        device = Device.filter_not_expired(identifier=raw["iss"]).first()
        if not device:
            raise ValidationError("Device not found")
        try:
            for token in DeviceToken.filter_not_expired(
                device__device=device,
                device__connector=self.stage.executor.current_stage.connector,
            ).values_list("key", flat=True):
                decoded = decode(
                    response,
                    key=token,
                    algorithms="HS512",
                    issuer=device.identifier,
                )
                if not compare_digest(
                    decoded["atc"],
                    self.stage.executor.plan.context[PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE],
                ):
                    raise ValidationError("Invalid challenge response")
                self.stage.executor.plan.context[PLAN_CONTEXT_DEVICE] = device
                return decoded
        except PyJWTError as exc:
            self.stage.logger.warning("failed to validate device challenge response", exc=exc)
            raise ValidationError("Invalid challenge response") from None


class AuthenticatorEndpointStageView(ChallengeStageView):
    """Endpoint stage"""

    response_class = EndpointAgentChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        stage: EndpointStage = self.executor.current_stage
        keypair = CertificateKeyPair.objects.get(pk=stage.connector.challenge_key_id)
        challenge_str = generate_id()
        challenge = encode(
            {
                "atc": challenge_str,
                "iss": str(stage.pk),
            },
            key=keypair.private_key,
            algorithm=JWTAlgorithms.from_private_key(keypair.private_key),
        )
        self.executor.plan.context[PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE] = challenge
        return EndpointAgentChallenge(
            data={
                "component": "ak-stage-endpoint-agent",
                "challenge": challenge,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        self.executor.plan.context.pop(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, None)
        return self.executor.stage_ok()
