from typing import Any

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from authentik.enterprise.stages.authenticator_endpoint_gdtc.views.dtc import (
    PLAN_CONTEXT_METHOD_ARGS_ENDPOINTS,
)
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    FrameChallenge,
    FrameChallengeResponse,
    HttpChallengeResponse,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD_ARGS


class AuthenticatorEndpointStageView(ChallengeStageView):
    """Endpoint stage"""

    response_class = FrameChallengeResponse

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        method_args = self.executor.plan.context.get(PLAN_CONTEXT_METHOD_ARGS, {})
        if method_args.get(PLAN_CONTEXT_METHOD_ARGS_ENDPOINTS):
            return self.executor.stage_ok()
        return super().dispatch(request, *args, **kwargs)

    def get_challenge(self, *args, **kwargs) -> Challenge:
        return FrameChallenge(
            data={
                "component": "xak-flow-frame",
                "url": self.request.build_absolute_uri(
                    reverse("authentik_stages_authenticator_endpoint_gdtc:chrome")
                ),
                "loading_overlay": True,
                "loading_text": _("Verifying your browser..."),
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        challenge = self._get_challenge()
        challenge.is_valid()
        return HttpChallengeResponse(challenge)
