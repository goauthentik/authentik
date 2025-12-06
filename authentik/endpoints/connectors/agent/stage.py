from datetime import timedelta
from hmac import compare_digest

from django.http import HttpResponse
from django.utils.timezone import now
from jwt import PyJWTError, decode, encode
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField

from authentik.crypto.models import CertificateKeyPair
from authentik.endpoints.connectors.agent.models import DeviceToken
from authentik.endpoints.models import Device, EndpointStage, StageMode
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
)
from authentik.flows.planner import PLAN_CONTEXT_DEVICE
from authentik.flows.stage import ChallengeStageView
from authentik.lib.generators import generate_id
from authentik.lib.utils.time import timedelta_from_string
from authentik.providers.oauth2.models import JWTAlgorithms

PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE = "goauthentik.io/endpoints/connectors/agent/challenge"
QS_CHALLENGE = "challenge"
QS_CHALLENGE_RESPONSE = "response"


class EndpointAgentChallenge(Challenge):
    """Signed challenge for authentik agent to respond to"""

    component = CharField(default="ak-stage-endpoint-agent")
    challenge = CharField()
    challenge_idle_timeout = IntegerField()


class EndpointAgentChallengeResponse(ChallengeResponse):
    """Response to signed challenge"""

    component = CharField(default="ak-stage-endpoint-agent")
    response = CharField(required=False, allow_null=True)

    def validate_response(self, response: str | None) -> Device | None:
        if not response:
            return None
        try:
            raw = decode(
                response,
                options={"verify_signature": False},
                audience="goauthentik.io/platform/endpoint",
            )
        except PyJWTError as exc:
            self.stage.logger.warning("Could not parse response", exc=exc)
            raise ValidationError("Invalid challenge response") from None
        device = Device.objects.filter(identifier=raw["iss"]).first()
        if not device:
            self.stage.logger.warning("Could not find device for challenge")
            raise ValidationError("Invalid challenge response")
        for token in DeviceToken.objects.filter(
            device__device=device,
            device__connector=self.stage.executor.current_stage.connector,
        ).values_list("key", flat=True):
            try:
                decoded = decode(
                    response,
                    key=token,
                    algorithms="HS512",
                    issuer=device.identifier,
                    audience="goauthentik.io/platform/endpoint",
                )
                if not compare_digest(
                    decoded["atc"],
                    self.stage.executor.plan.context[PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE],
                ):
                    self.stage.logger.warning("mismatched challenge")
                    raise ValidationError("Invalid challenge response")
                return device
            except PyJWTError as exc:
                self.stage.logger.warning("failed to validate device challenge response", exc=exc)
        raise ValidationError("Invalid challenge response")


class AuthenticatorEndpointStageView(ChallengeStageView):
    """Endpoint stage"""

    response_class = EndpointAgentChallengeResponse

    def get(self, request, *args, **kwargs):
        stage: EndpointStage = self.executor.current_stage
        keypair = CertificateKeyPair.objects.filter(pk=stage.connector.challenge_key_id).first()
        if not keypair:
            return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs) -> Challenge:
        stage: EndpointStage = self.executor.current_stage
        keypair = CertificateKeyPair.objects.get(pk=stage.connector.challenge_key_id)
        challenge_str = generate_id()
        iat = now()
        challenge = encode(
            {
                "atc": challenge_str,
                "iss": str(stage.pk),
                "iat": int(iat.timestamp()),
                "exp": int((iat + timedelta(minutes=5)).timestamp()),
                "goauthentik.io/device/check_in": stage.connector.challenge_trigger_check_in,
            },
            headers={"kid": keypair.kid},
            key=keypair.private_key,
            algorithm=JWTAlgorithms.from_private_key(keypair.private_key),
        )
        self.executor.plan.context[PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE] = challenge
        return EndpointAgentChallenge(
            data={
                "component": "ak-stage-endpoint-agent",
                "challenge": challenge,
                "challenge_idle_timeout": int(
                    timedelta_from_string(stage.connector.challenge_idle_timeout).total_seconds()
                ),
            }
        )

    def challenge_invalid(self, response: EndpointAgentChallengeResponse) -> HttpResponse:
        if self.executor.current_stage.mode == StageMode.OPTIONAL:
            return self.executor.stage_ok()
        return super().challenge_invalid(response)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        if device := response.validated_data.get("response"):
            self.executor.plan.context[PLAN_CONTEXT_DEVICE] = device
        elif self.executor.current_stage.mode == StageMode.REQUIRED:
            return self.executor.stage_invalid("Invalid challenge response")
        return self.executor.stage_ok()

    def cleanup(self):
        self.executor.plan.context.pop(PLAN_CONTEXT_AGENT_ENDPOINT_CHALLENGE, None)
