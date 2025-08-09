"""SAML Logout Response Stage"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from authentik.flows.challenge import (
    PLAN_CONTEXT_TITLE,
    AutosubmitChallenge,
    AutoSubmitChallengeResponse,
    Challenge,
    ChallengeResponse,
)
from authentik.flows.stage import ChallengeStageView
from authentik.policies.utils import delete_none_values
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.logout_response_processor import LogoutResponseProcessor
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode, nice64
from authentik.providers.saml.views.flows import (
    REQUEST_KEY_RELAY_STATE,
    REQUEST_KEY_SAML_RESPONSE,
)


class SAMLLogoutResponseStage(ChallengeStageView):
    """Stage that generates and sends SAML LogoutResponse

    This stage sends the LogoutResponse to the SP using the configured binding.
    It does not end the authentik session.
    """

    response_class = AutoSubmitChallengeResponse

    def get(self, request: HttpRequest) -> HttpResponse:
        """Process the logout and send response"""

        # Check if we have a logout request in session or plan context
        logout_request = self.executor.plan.context.get("logout_request")

        if not logout_request:
            return self.executor.stage_ok()

        provider: SAMLProvider = self.executor.plan.context.get("provider")

        if not provider.sls_url:
            return self.executor.stage_ok()

        # Generate LogoutResponse
        processor = LogoutResponseProcessor(provider, logout_request)
        response_xml = processor.build_response(status="Success", destination=provider.sls_url)

        # Use the SLS binding configured for the provider
        if provider.sls_binding == SAMLBindings.POST:
            # POST binding - use autosubmit form
            form_attrs = delete_none_values(
                {
                    REQUEST_KEY_SAML_RESPONSE: nice64(response_xml),
                    REQUEST_KEY_RELAY_STATE: logout_request.relay_state,
                }
            )
            return super().get(
                self.request,
                **{
                    "component": "ak-stage-autosubmit",
                    "title": self.executor.plan.context.get(
                        PLAN_CONTEXT_TITLE,
                        _("Logging out..."),
                    ),
                    "url": provider.sls_url,
                    "attrs": form_attrs,
                },
            )
        elif provider.sls_binding == SAMLBindings.REDIRECT:
            # REDIRECT binding - direct redirect
            url_args = {
                REQUEST_KEY_SAML_RESPONSE: deflate_and_base64_encode(response_xml),
            }
            if logout_request.relay_state:
                url_args[REQUEST_KEY_RELAY_STATE] = logout_request.relay_state

            # Some url's ask for requests to be sent to domain.com/page?sls
            if "?" in provider.sls_url:
                separator = "&"
            else:
                separator = "?"

            querystring = urlencode(url_args)
            redirect_url = f"{provider.sls_url}{separator}{querystring}"

            return redirect(redirect_url)

        return self.executor.stage_invalid()

    def get_challenge(self, **kwargs) -> Challenge:
        """Return the challenge - this will render the auto-submit form"""
        return AutosubmitChallenge(data=kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """This is called when the challenge form is submitted back to authentik
        For POST binding, we've already sent the form to the SP, so this shouldn't be reached
        For safety, we'll just continue the flow"""
        return self.executor.stage_ok()
