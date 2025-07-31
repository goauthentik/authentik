"""SAML Logout stages for automatic injection"""

from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.fields import CharField, DictField, IntegerField, ListField
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.stage import ChallengeStageView, StageView
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.sources.saml.processors.constants import SAML_NAME_ID_FORMAT_EMAIL

LOGGER = get_logger()


class SAMLLogoutStageView(StageView):
    """SAML Logout stage that handles redirect chain logout"""

    def get_pending_providers(self) -> list[str]:
        """Get list of SAML providers that need logout"""
        # Get from session or initialize
        pending = self.request.session.get("saml_logout_pending", None)
        if pending is None:
            # Query all SAML providers with logout URLs
            providers = SAMLProvider.objects.filter(
                application__isnull=False,
                sls_url__isnull=False,
            ).exclude(sls_url="")
            pending = [str(p.pk) for p in providers]
            self.request.session["saml_logout_pending"] = pending
        return pending

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Handle POST request for IDP-initiated logout"""
        # For IDP-initiated logout, POST and GET are the same
        # The user is initiating logout from authentik's side
        if "SAMLResponse" in request.POST:
            # This is a response from the SP, just continue to next provider
            LOGGER.debug("Received SAML logout response, continuing to next provider")
        return self.get(request, application_slug)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET request - redirect to next provider or finish"""
        # Check if this is a SAML logout response
        if "SAMLResponse" in request.GET:
            # This is a response from the SP, just continue to next provider
            LOGGER.debug("Received SAML logout response, continuing to next provider")
            # The pending list was already updated when we sent the request

        pending = self.get_pending_providers()
        if not pending:
            # All done, clean up and continue flow
            self.request.session.pop("saml_logout_pending", None)
            return self.executor.stage_ok()

        # Get next provider
        provider_pk = pending.pop(0)
        self.request.session["saml_logout_pending"] = pending

        try:
            provider = SAMLProvider.objects.get(pk=provider_pk)
            # Generate return URL back to this stage using the interface URL
            return_url = self.request.build_absolute_uri(
                reverse("authentik_core:if-flow", kwargs={"flow_slug": self.executor.flow.slug})
            )

            # Determine NameID
            user = self.request.user
            name_id = user.email
            name_id_format = SAML_NAME_ID_FORMAT_EMAIL

            if provider.name_id_mapping:
                try:
                    value = provider.name_id_mapping.evaluate(
                        user=user,
                        request=self.request,
                        provider=provider,
                    )
                    if value is not None:
                        name_id = str(value)
                except Exception as exc:
                    LOGGER.warning("Failed to evaluate name_id_mapping", exc=exc, provider=provider)

            # Create SAML logout request
            processor = LogoutRequestProcessor(
                provider=provider,
                user=user,
                destination=provider.sls_url,
                name_id=name_id,
                name_id_format=name_id_format,
                relay_state=return_url,
            )

            if provider.sls_binding == "post":
              # For POST binding, return an auto-submit form
              encoded_request = processor.encode_post()
              html = f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>SAML Logout</title>
                </head>
                <body onload="document.getElementById('samlForm').submit();">
                    <form id="samlForm" method="post" action="{escape(provider.sls_url)}">
                        <input type="hidden" name="SAMLRequest" value="{escape(encoded_request)}"/>
                        <input type="hidden" name="RelayState" value="{escape(return_url)}"/>
                        <noscript>
                            <p>Please click continue to complete logout from {escape(provider.name)}.</p>
                            <input type="submit" value="Continue"/>
                        </noscript>
                    </form>
                    <script>
                        console.log('Submitting SAML logout form');
                        document.getElementById('samlForm').submit();
                    </script>
                </body>
                </html>"""
              return HttpResponse(html, content_type="text/html")
            else:
                # Build redirect URL with proper SAML parameters
                encoded_request = processor.encode_redirect()
                params = {"SAMLRequest": encoded_request, "RelayState": return_url}

                # Check if the SLS URL already has query parameters
                if "?" in provider.sls_url:
                    logout_url = f"{provider.sls_url}&{urlencode(params)}"
                else:
                    logout_url = f"{provider.sls_url}?{urlencode(params)}"

                LOGGER.debug(
                    "Redirecting to provider for SAML logout",
                    provider=provider.name,
                    logout_url=logout_url,
                )
                return redirect(logout_url)
        except SAMLProvider.DoesNotExist:
            # Provider deleted? Skip and continue
            return self.get(request, *args, **kwargs)

class SAMLIframeLogoutChallenge(Challenge):
    """Challenge for SAML iframe logout"""

    component = CharField(default="ak-stage-saml-iframe-logout")
    logout_urls = ListField(child=DictField())
    timeout = IntegerField()


class SAMLIframeLogoutChallengeResponse(ChallengeResponse):
    """Response for SAML iframe logout"""

    component = CharField(default="ak-stage-saml-iframe-logout")


class SAMLIframeLogoutStageView(ChallengeStageView):
    """SAML Logout stage that handles parallel iframe logout"""

    response_class = SAMLIframeLogoutChallengeResponse

    def __init__(self, executor, **kwargs):
        super().__init__(executor, **kwargs)
        self.iframe_timeout = kwargs.get("iframe_timeout", 5000)

    def get_challenge(self) -> Challenge:
        """Generate iframe logout challenge"""
        providers = SAMLProvider.objects.filter(
            application__isnull=False,
            sls_url__isnull=False,
        ).exclude(sls_url="")

        return_url = self.request.build_absolute_uri(
                reverse("authentik_core:if-flow", kwargs={"flow_slug": self.executor.flow.slug})
            )

        logout_urls = []
        for provider in providers:
            try:
                # Determine NameID
                user = self.request.user
                name_id = user.email
                name_id_format = SAML_NAME_ID_FORMAT_EMAIL

                if provider.name_id_mapping:
                    try:
                        value = provider.name_id_mapping.evaluate(
                            user=user,
                            request=self.request,
                            provider=provider,
                        )
                        if value is not None:
                            name_id = str(value)
                    except Exception as exc:
                        LOGGER.warning("Failed to evaluate name_id_mapping", exc=exc, provider=provider)

                # Create SAML logout request
                processor = LogoutRequestProcessor(
                    provider=provider,
                    user=user,
                    destination=provider.sls_url,
                    name_id=name_id,
                    name_id_format=name_id_format,
                    relay_state=return_url
                )

                # Build redirect URL with proper SAML parameters
                if provider.sls_binding == "redirect":
                    encoded_request = processor.encode_redirect()
                    params = {"SAMLRequest": encoded_request, "relayState": return_url}
                    # Check if the SLS URL already has query parameters
                    if "?" in provider.sls_url:
                        logout_url = f"{provider.sls_url}&{urlencode(params)}"
                    else:
                        logout_url = f"{provider.sls_url}?{urlencode(params)}"
                    logout_urls.append(
                        {
                            "url": logout_url,
                            "provider_name": provider.name,
                            "binding": "redirect"
                        }
                    )
                elif provider.sls_binding == "post":
                    encoded_request = processor.encode_post()
                    logout_urls.append(
                        {
                            "url": provider.sls_url,
                            "saml_request": encoded_request,
                            "provider_name": provider.name,
                            "binding": "post"
                        }
                    )

            except Exception as exc:
                LOGGER.warning("Failed to generate logout URL", provider=provider, exc=exc)

        return SAMLIframeLogoutChallenge(
            data={
                "component": "ak-stage-saml-iframe-logout",
                "logout_urls": logout_urls,
                "timeout": self.iframe_timeout,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:  # noqa: ARG002
        """Iframe logout completed"""
        return self.executor.stage_ok()
