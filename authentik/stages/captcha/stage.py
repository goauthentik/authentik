"""authentik captcha stage"""

from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from requests import RequestException
from rest_framework.fields import BooleanField, CharField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger

from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallengeMixin,
)
from authentik.flows.stage import ChallengeStageView
from authentik.lib.utils.http import get_http_session
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.captcha.models import CaptchaStage

LOGGER = get_logger()
PLAN_CONTEXT_CAPTCHA = "captcha"


class CaptchaChallenge(WithUserInfoChallengeMixin, Challenge):
    """Site public key"""

    component = CharField(default="ak-stage-captcha")

    site_key = CharField(required=True)
    js_url = CharField(required=True)
    interactive = BooleanField(required=True)


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
                error_codes = data.get("error-codes", ["unknown-error"])
                LOGGER.warning("Failed to verify captcha token", error_codes=error_codes)

                # These cases can usually be fixed by simply requesting a new token and retrying.
                # [reCAPTCHA](https://developers.google.com/recaptcha/docs/verify#error_code_reference)
                # [hCaptcha](https://docs.hcaptcha.com/#siteverify-error-codes-table)
                # [Turnstile](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/#error-codes)
                retriable_error_codes = [
                    "missing-input-response",
                    "invalid-input-response",
                    "timeout-or-duplicate",
                    "expired-input-response",
                    "already-seen-response",
                ]

                if set(error_codes).issubset(set(retriable_error_codes)):
                    error_message = _("Invalid captcha response. Retrying may solve this issue.")
                else:
                    error_message = _("Invalid captcha response")
                raise ValidationError(error_message)
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
                "interactive": self.executor.current_stage.interactive,
            }
        )

    def challenge_valid(self, response: CaptchaChallengeResponse) -> HttpResponse:
        response = response.validated_data["token"]
        self.executor.plan.context[PLAN_CONTEXT_CAPTCHA] = {
            "response": response,
            "stage": self.executor.current_stage,
        }
        return self.executor.stage_ok()
