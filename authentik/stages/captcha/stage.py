"""authentik captcha stage"""

from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from requests import RequestException
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.http import get_http_session
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.captcha.models import CaptchaStage

PLAN_CONTEXT_CAPTCHA = "captcha"


class CaptchaChallenge(WithUserInfoChallenge):
    """Site public key"""

    site_key = CharField()
    js_url = CharField()
    component = CharField(default="ak-stage-captcha")


def get_friendly_captcha_error(error: str) -> str:
    match error:
        case "missing-input-secret":
            return _("Secret was not provided. This is likely a misconfiguration error.")
        case "invalid-input-secret":
            return _("Secret was invalid. This is likely a misconfiguration error.")
        case "missing-input-response":
            return _("Client response was not provided. Try again.")
        case "invalid-input-response":
            return _("Client response was invalid. Try again.")
        case "timeout-or-duplicate":
            return _("Client response has timed out or was already used. Try again.")

    return _("Unknown error")


def verify_captcha_token(stage: CaptchaStage, token: str, remote_ip: str):
    """Validate captcha token"""
    try:
        response = get_http_session().post(
            stage.api_url,
            headers={
                "Content-type": "application/x-www-form-urlencoded",
            },
            data={
                "secret": stage.private_key,
                "response": token,
                "remoteip": remote_ip,
            },
        )
        response.raise_for_status()
        data = response.json()
        if stage.error_on_invalid_score:
            if not data.get("success", False):
                error_codes = data.get("error-codes", ["Unknown error"])
                raise ValidationError(
                    _(
                        "Invalid captcha response: {error}".format(
                            error="".join(map(get_friendly_captcha_error, error_codes))
                        )
                    )
                )
            if "score" in data:
                score = float(data.get("score"))
                if stage.score_max_threshold > -1 and score > stage.score_max_threshold:
                    raise ValidationError(_("Invalid captcha response"))
                if stage.score_min_threshold > -1 and score < stage.score_min_threshold:
                    raise ValidationError(_("Invalid captcha response"))
    except (RequestException, TypeError) as exc:
        raise ValidationError(_("Failed to validate token")) from exc

    return data


class CaptchaChallengeResponse(ChallengeResponse):
    """Validate captcha token"""

    token = CharField()
    component = CharField(default="ak-stage-captcha")

    def validate_token(self, token: str) -> str:
        """Validate captcha token"""
        stage: CaptchaStage = self.stage.executor.current_stage
        client_ip = ClientIPMiddleware.get_client_ip(self.stage.request)

        return verify_captcha_token(stage, token, client_ip)


class CaptchaStageView(ChallengeStageView):
    """Simple captcha checker, logic is handled in django-captcha module"""

    response_class = CaptchaChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return CaptchaChallenge(
            data={
                "js_url": self.executor.current_stage.js_url,
                "site_key": self.executor.current_stage.public_key,
            }
        )

    def challenge_valid(self, response: CaptchaChallengeResponse) -> HttpResponse:
        response = response.validated_data["token"]
        self.executor.plan.context[PLAN_CONTEXT_CAPTCHA] = {
            "response": response,
            "stage": self.executor.current_stage,
        }
        return self.executor.stage_ok()
