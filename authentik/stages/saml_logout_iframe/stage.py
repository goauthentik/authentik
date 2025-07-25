"""SAML iframe logout stage logic"""

from urllib.parse import urlencode

from django.http import HttpResponse
from rest_framework.fields import CharField, DictField, IntegerField, ListField
from structlog.stdlib import get_logger

from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.sources.saml.processors.constants import SAML_NAME_ID_FORMAT_EMAIL

LOGGER = get_logger()


class SAMLIframeLogoutChallenge(Challenge):
    """Challenge to render iframes for SAML logout"""

    component = CharField(default="ak-stage-saml-iframe-logout")
    logout_urls = ListField(child=DictField(), required=False)
    timeout = IntegerField(default=5000)


class SAMLIframeLogoutChallengeResponse(ChallengeResponse):
    """Response when all iframes have completed"""

    component = CharField(default="ak-stage-saml-iframe-logout")


class SAMLIframeLogoutStageView(ChallengeStageView):
    """SAML iframe logout stage - handles SAML logout using iframes"""

    response_class = SAMLIframeLogoutChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Generate the challenge with logout URLs"""

        # Check if user is authenticated
        if not self.request.user.is_authenticated:
            LOGGER.debug("User not authenticated, skipping SAML iframe logout")
            # Return empty challenge that will auto-submit
            return SAMLIframeLogoutChallenge(
                data={
                    "logout_urls": [],
                    "timeout": 0,
                }
            )

        # Get the actual user object (handle SimpleLazyObject)
        user = self.request.user
        if hasattr(user, "_wrapped"):
            actual_user = user._wrapped
            if actual_user is None:
                _ = user.pk
                actual_user = user
        else:
            actual_user = user

        # Get all SAML providers that need iframe logout
        # Support both POST and REDIRECT bindings
        providers = SAMLProvider.objects.filter(
            application__isnull=False,
            sls_url__isnull=False,
            sls_binding__in=[SAMLBindings.POST, SAMLBindings.REDIRECT],
        ).exclude(sls_url="")

        # Debug: Check all SAML providers
        all_providers = SAMLProvider.objects.all()
        LOGGER.info(
            "Debug: All SAML providers in system",
            total_count=all_providers.count(),
            providers=[
                {
                    "name": p.name,
                    "has_app": p.application is not None,
                    "sls_url": p.sls_url,
                    "sls_binding": p.sls_binding,
                }
                for p in all_providers
            ],
        )

        LOGGER.info(
            "Found SAML providers for iframe logout",
            provider_count=providers.count(),
            providers=[(p.name, p.sls_binding) for p in providers],
        )

        logout_urls = []

        for provider in providers:
            try:
                # Determine NameID
                name_id = actual_user.email
                name_id_format = SAML_NAME_ID_FORMAT_EMAIL

                if provider.name_id_mapping:
                    try:
                        value = provider.name_id_mapping.evaluate(
                            user=actual_user,
                            request=self.request,
                            provider=provider,
                        )
                        if value is not None:
                            name_id = str(value)
                    except Exception as exc:
                        LOGGER.warning(
                            "Failed to evaluate name_id_mapping", exc=exc, provider=provider
                        )

                # Create logout request processor
                processor = LogoutRequestProcessor(
                    provider=provider,
                    user=actual_user,
                    destination=provider.sls_url,
                    name_id=name_id,
                    name_id_format=name_id_format,
                    relay_state=None,
                )

                # Generate the SAML request based on binding type

                # Handle different bindings
                if provider.sls_binding == SAMLBindings.POST:
                    # Generate SAML request for POST binding
                    saml_request_encoded = processor.encode_post()
                    # For POST binding, we need the URL and SAML request data
                    logout_urls.append(
                        {
                            "url": provider.sls_url,
                            "saml_request": saml_request_encoded,
                            "provider_name": provider.name,
                            "binding": "POST",
                        }
                    )
                elif provider.sls_binding == SAMLBindings.REDIRECT:
                    # Generate SAML request for REDIRECT binding
                    saml_request_encoded = processor.encode_redirect()
                    # For REDIRECT binding, build the full URL with query parameters
                    params = {
                        "SAMLRequest": saml_request_encoded,
                    }
                    # Check if sls_url already has query parameters
                    if "?" in provider.sls_url:
                        # URL already has query params, append with &
                        full_url = f"{provider.sls_url}&{urlencode(params)}"
                    else:
                        # No query params yet, add with ?
                        full_url = f"{provider.sls_url}?{urlencode(params)}"
                    logout_urls.append(
                        {
                            "url": full_url,
                            "provider_name": provider.name,
                            "binding": "REDIRECT",
                        }
                    )

                LOGGER.info(
                    "Added provider for iframe logout",
                    provider=provider.name,
                    binding=provider.sls_binding,
                    sls_url=provider.sls_url,
                    name_id=name_id,
                )

            except Exception as exc:
                LOGGER.warning(
                    "Failed to generate logout URL for provider",
                    provider=provider.name,
                    exc=exc,
                )
                continue

        if not logout_urls:
            LOGGER.info("No providers require iframe logout")
            # Return empty challenge that will auto-submit
            return SAMLIframeLogoutChallenge(
                data={
                    "logout_urls": [],
                    "timeout": 0,
                }
            )

        # Get timeout from stage configuration
        stage = self.executor.current_stage
        timeout = stage.iframe_timeout if hasattr(stage, "iframe_timeout") else 5000

        LOGGER.info(
            "Returning iframe logout challenge",
            provider_count=len(logout_urls),
            timeout=timeout,
        )

        return SAMLIframeLogoutChallenge(
            data={
                "logout_urls": logout_urls,
                "timeout": timeout,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Handle response when all iframes are done"""
        LOGGER.debug("Iframe logout completed, continuing flow")
        return self.executor.stage_ok()
