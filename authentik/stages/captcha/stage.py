"""authentik captcha stage"""

from django.http.response import HttpResponse
from requests import RequestException, post
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError

from authentik import __version__
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.http import get_client_ip
from authentik.stages.captcha.models import CaptchaStage


class CaptchaChallenge(WithUserInfoChallenge):
    """Site public key"""

    site_key = CharField()


class CaptchaChallengeResponse(ChallengeResponse):
    """Validate captcha token"""

    token = CharField()

    def validate_token(self, token: str) -> str:
        """Validate captcha token"""
        stage: CaptchaStage = self.stage.executor.current_stage
        try:
            response = post(
                "https://www.google.com/recaptcha/api/siteverify",
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "User-agent": f"authentik {__version__} ReCaptcha",
                },
                data={
                    "secret": stage.private_key,
                    "response": token,
                    "remoteip": get_client_ip(self.stage.request),
                },
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("success", False):
                raise ValidationError(
                    f"Failed to validate token: {data.get('error-codes', '')}"
                )
        except RequestException as exc:
            raise ValidationError("Failed to validate token") from exc
        return token


class CaptchaStageView(ChallengeStageView):
    """Simple captcha checker, logic is handeled in django-captcha module"""

    response_class = CaptchaChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return CaptchaChallenge(
            data={
                "type": ChallengeTypes.native,
                "component": "ak-stage-captcha",
                "site_key": self.executor.current_stage.public_key,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()
