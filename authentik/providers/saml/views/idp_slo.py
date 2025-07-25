"""IDP-initiated SAML Single Logout Views"""

from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor

LOGGER = get_logger()


class IDPInitiatedSLOView(PolicyAccessView):
    """Handle IDP-initiated SAML Single Logout"""

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
        self.provider: SAMLProvider = get_object_or_404(
            SAMLProvider, pk=self.application.provider_id
        )

    def get(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Handle IDP-initiated logout"""
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return redirect("authentik_core:root-redirect")

        # Check if provider supports logout
        if not self.provider.sls_url:
            LOGGER.error(
                "No SLS URL configured for IDP-initiated logout",
                provider=self.provider,
                application=self.application,
            )
            return bad_request_message(request, "Provider does not support logout")

        LOGGER.info(
            "Starting IDP-initiated logout",
            user=request.user,
            provider=self.provider,
            application=self.application,
        )

        # Create a LogoutRequest to send to the SP
        logout_processor = LogoutRequestProcessor(
            provider=self.provider,
            user=request.user,
            destination=self.provider.sls_url,
            relay_state=None,  # No relay state for IDP-initiated
        )

        # Determine binding type and send appropriately
        if self.provider.sls_binding == SAMLBindings.REDIRECT:
            # Redirect binding - send via URL parameters
            saml_request = logout_processor.encode_redirect()
            params = {
                "SAMLRequest": saml_request,
            }

            # Check if the destination URL already has query parameters
            if "?" in self.provider.sls_url:
                redirect_url = f"{self.provider.sls_url}&{urlencode(params)}"
            else:
                redirect_url = f"{self.provider.sls_url}?{urlencode(params)}"

            return redirect(redirect_url)
        else:
            # POST binding - send via auto-submit form
            saml_request = logout_processor.encode_post()

            html = f"""
            <html>
                <body onload="document.forms[0].submit()">
                    <form method="post" action="{self.provider.sls_url}">
                        <input type="hidden" name="SAMLRequest" value="{saml_request}" />
                        <noscript>
                            <input type="submit" value="Continue" />
                        </noscript>
                    </form>
                </body>
            </html>
            """

            return HttpResponse(html, content_type="text/html")

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Handle POST request for IDP-initiated logout"""
        # For IDP-initiated logout, POST and GET are the same
        # The user is initiating logout from authentik's side
        return self.get(request, application_slug)
