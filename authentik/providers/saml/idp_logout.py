"""SAML Logout stages for automatic injection"""

import base64

from django.http import HttpResponse
from django.urls import reverse
from rest_framework.fields import CharField, DictField, ListField
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.challenge import Challenge, ChallengeResponse, HttpChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor

LOGGER = get_logger()


class SAMLLogoutStageViewBase(ChallengeStageView):
    """Base class for SAML logout stages with shared functionality"""

    def _create_logout_processor(
        self,
        provider: SAMLProvider,
        user: User | None,
        name_id: str,
        name_id_format: str,
        session_index: str,
        relay_state: str,
    ) -> LogoutRequestProcessor:
        """Create a LogoutRequestProcessor with common parameters"""
        return LogoutRequestProcessor(
            provider=provider,
            user=user,
            destination=provider.sls_url,
            name_id=name_id,
            name_id_format=name_id_format,
            session_index=session_index,
            relay_state=relay_state,
        )


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


class SAMLLogoutStageView(SAMLLogoutStageViewBase):
    """SAML Logout stage that handles redirect chain logout.
    Also supports frontchannel post"""

    response_class = SAMLLogoutChallengeResponse

    def encode_relay_state(self, return_url: str) -> str:
        """Encode return URL into RelayState"""
        return base64.urlsafe_b64encode(return_url.encode()).decode()

    def decode_relay_state(self, relay_state: str) -> str:
        """Decode RelayState to get return URL"""
        try:
            return base64.urlsafe_b64decode(relay_state.encode()).decode()
        except Exception as exc:
            LOGGER.warning("Failed to decode relay state", exc=exc)
            return ""

    def get_pending_providers(self) -> list[dict]:
        """Get list of SAML providers that need logout"""
        # Get logouts off of anonymous session
        return self.request.session.get("saml_logout_pending", [])

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Generate challenge for next provider"""
        pending = self.get_pending_providers()
        if not pending:
            # All done, return completion challenge
            return SAMLLogoutChallenge(
                data={
                    "component": "ak-stage-saml-logout",
                    "is_complete": "true",
                }
            )

        session_data = pending.pop(0)
        self.request.session["saml_logout_pending"] = pending

        try:
            provider = SAMLProvider.objects.get(pk=session_data["provider_pk"])
            # Generate return URL back to this stage using the interface URL
            return_url = self.request.build_absolute_uri(
                reverse("authentik_core:if-flow", kwargs={"flow_slug": self.executor.flow.slug})
            )

            # Store return URL in session as fallback if SP doesn't echo RelayState
            self.request.session["saml_logout_return_url"] = return_url

            # Use stored session data (user is already logged out)
            name_id = session_data["name_id"]
            name_id_format = session_data["name_id_format"]
            session_index = session_data["session_index"]

            # Encode return URL in relay state
            relay_state = self.encode_relay_state(return_url)

            # Create SAML logout request
            processor = self._create_logout_processor(
                provider=provider,
                user=None,  # User is already logged out
                name_id=name_id,
                name_id_format=name_id_format,
                session_index=session_index,
                relay_state=relay_state,
            )

            if provider.sls_binding == "post":
                # For POST binding, return challenge with form data
                form_data = processor.get_post_form_data()
                return SAMLLogoutChallenge(
                    data={
                        "component": "ak-stage-saml-logout",
                        "url": provider.sls_url,
                        "saml_request": form_data["SAMLRequest"],
                        "relay_state": form_data["RelayState"],
                        "provider_name": provider.name,
                        "binding": "post",
                    }
                )
            else:
                # Build redirect URL with proper SAML parameters and signature if needed
                logout_url = processor.get_redirect_url()

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
        except Exception as exc:
            # Log any error and skip to next provider
            LOGGER.error(
                "Failed to process logout for provider",
                exc=exc,
                provider_pk=session_data.get("provider_pk"),
            )
            return self.get_challenge(*args, **kwargs)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Challenge completed"""
        # When we get here, it means the frontend has processed a challenge
        # If it was the "complete" binding, we're done
        # Otherwise, we need to get the next challenge
        # Get the next challenge
        challenge = self.get_challenge()

        # Validate the challenge
        if not challenge.is_valid():
            LOGGER.error("Invalid challenge", errors=challenge.errors)
            return self.executor.stage_invalid()

        # If is_complete is true, we're done with all providers
        if challenge.initial_data.get("is_complete") == "true":
            LOGGER.debug("All SAML providers logged out, completing stage")
            # Delete the anonymous session
            self.request.session.flush()
            return self.executor.stage_ok()

        # Otherwise, return the next challenge
        return HttpChallengeResponse(challenge)


class SAMLIframeLogoutChallenge(Challenge):
    """Challenge for SAML iframe logout"""

    component = CharField(default="ak-stage-saml-iframe-logout")
    logout_urls = ListField(child=DictField())


class SAMLIframeLogoutChallengeResponse(ChallengeResponse):
    """Response for SAML iframe logout"""

    component = CharField(default="ak-stage-saml-iframe-logout")


class SAMLIframeLogoutStageView(SAMLLogoutStageViewBase):
    """SAML Logout stage that handles parallel iframe logout"""

    response_class = SAMLIframeLogoutChallengeResponse

    def _process_session_for_logout(
        self, session_data: dict, user: User | None, return_url: str
    ) -> dict | None:
        """Process a single session and return logout data"""
        try:
            provider = SAMLProvider.objects.get(pk=session_data["provider_pk"])

            processor = self._create_logout_processor(
                provider=provider,
                user=user,
                name_id=session_data["name_id"],
                name_id_format=session_data["name_id_format"],
                session_index=session_data.get("session_index", ""),
                relay_state=return_url,
            )

            if provider.sls_binding == "post":
                form_data = processor.get_post_form_data()
                return {
                    "url": provider.sls_url,
                    "saml_request": form_data["SAMLRequest"],
                    "provider_name": provider.name,
                    "binding": "post",
                    "relay_state": form_data["RelayState"],
                }
            else:
                logout_url = processor.get_redirect_url()
                return {
                    "url": logout_url,
                    "provider_name": provider.name,
                    "binding": "redirect",
                }
        except Exception as exc:
            LOGGER.warning(
                "Failed to generate logout URL",
                provider_pk=session_data.get("provider_pk"),
                exc=exc,
            )
            return None

    def get_challenge(self) -> Challenge:
        """Generate iframe logout challenge"""
        return_url = self.request.build_absolute_uri(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.executor.flow.slug})
        )

        logout_urls = []

        pending = self.request.session.get("saml_logout_pending", [])
        for session_data in pending:
            logout_data = self._process_session_for_logout(
                session_data, user=None, return_url=return_url
            )
            if logout_data:
                logout_urls.append(logout_data)
        return SAMLIframeLogoutChallenge(
            data={
                "component": "ak-stage-saml-iframe-logout",
                "logout_urls": logout_urls,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Iframe logout completed"""
        # Delete the anonymous session
        self.request.session.flush()
        return self.executor.stage_ok()
