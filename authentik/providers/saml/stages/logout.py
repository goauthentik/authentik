"""SAML Logout stages for automatic injection"""

from urllib.parse import urlencode

from django.http import HttpResponse
from django.urls import reverse
from rest_framework.fields import CharField, DictField, IntegerField, ListField
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.sources.saml.processors.constants import SAML_NAME_ID_FORMAT_EMAIL

LOGGER = get_logger()


class SAMLLogoutChallenge(Challenge):
    """Challenge for SAML logout"""

    component = CharField(default="ak-stage-saml-logout")
    url = CharField(required=False)
    saml_request = CharField(required=False)
    relay_state = CharField(required=False)
    provider_name = CharField(required=False)
    binding = CharField(required=False)
    redirect_url = CharField(required=False)
    is_complete = CharField(required=False, default="false")


class SAMLLogoutChallengeResponse(ChallengeResponse):
    """Response for SAML logout"""

    component = CharField(default="ak-stage-saml-logout")


class SAMLLogoutStageView(ChallengeStageView):
    """SAML Logout stage that handles redirect chain logout"""

    response_class = SAMLLogoutChallengeResponse

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

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Generate challenge for next provider"""
        # Check if this is a SAML logout response
        if "SAMLResponse" in self.request.GET or "SAMLResponse" in self.request.POST:
            # This is a response from the SP, just continue to next provider
            LOGGER.debug("Received SAML logout response, continuing to next provider")
            # The pending list was already updated when we sent the request

        pending = self.get_pending_providers()
        if not pending:
            # All done, return completion challenge (don't clean up session yet)
            return SAMLLogoutChallenge(
                data={
                    "component": "ak-stage-saml-logout",
                    "is_complete": "true",
                }
            )

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
                # For POST binding, return challenge with form data
                encoded_request = processor.encode_post()
                return SAMLLogoutChallenge(
                    data={
                        "component": "ak-stage-saml-logout",
                        "url": provider.sls_url,
                        "saml_request": encoded_request,
                        "relay_state": return_url,
                        "provider_name": provider.name,
                        "binding": "post",
                    }
                )
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

                return SAMLLogoutChallenge(
                    data={
                        "component": "ak-stage-saml-logout",
                        "redirect_url": logout_url,
                        "provider_name": provider.name,
                        "binding": "redirect",
                    }
                )
        except SAMLProvider.DoesNotExist:
            # Provider deleted? Skip and continue
            return self.get_challenge(*args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Challenge completed"""
        # When we get here, it means the frontend has processed a challenge
        # If it was the "complete" binding, we're done
        # Otherwise, we need to get the next challenge
        from authentik.flows.challenge import HttpChallengeResponse

        # Get the next challenge
        challenge = self.get_challenge()

        # Validate the challenge
        if not challenge.is_valid():
            LOGGER.error("Invalid challenge", errors=challenge.errors)
            return self.executor.stage_invalid()

        # If is_complete is true, we're done with all providers
        if challenge.initial_data.get("is_complete") == "true":
            LOGGER.debug("All SAML providers logged out, completing stage")
            # Clean up session before completing
            self.request.session.pop("saml_logout_pending", None)
            self.request.session.save()
            return self.executor.stage_ok()

        # Otherwise, return the next challenge
        return HttpChallengeResponse(challenge)


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
