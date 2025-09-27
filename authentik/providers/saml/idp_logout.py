"""SAML and OIDC Logout stages for automatic injection"""

import base64
from urllib.parse import urlencode

from django.http import HttpResponse
from django.urls import reverse
from rest_framework.fields import BooleanField, CharField, DictField, ListField
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.flows.challenge import Challenge, ChallengeResponse, HttpChallengeResponse
from authentik.flows.stage import ChallengeStageView
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.saml.models import SAMLBindings, SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.views.flows import (
    PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS,
    SESSION_KEY_SAML_LOGOUT_RETURN,
)

LOGGER = get_logger()

# Import OIDC context key
PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS = "oidc_logout_iframe_sessions"


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
    is_complete = BooleanField(required=False, default=False)


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
        except (ValueError, UnicodeDecodeError) as exc:
            LOGGER.warning("Failed to decode relay state", exc=exc)
            return ""

    def get_pending_providers(self) -> list[dict]:
        """Get list of SAML providers that need to front-channel redirect logout"""
        return self.executor.plan.context.get(PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS, [])

    def get_challenge(self, *args, **kwargs) -> Challenge:
        """Generate challenge for next provider"""
        pending = self.get_pending_providers()
        if not pending:
            self.executor.plan.context.pop(PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS, None)
            return SAMLLogoutChallenge(
                data={
                    "component": "ak-stage-saml-logout",
                    "is_complete": True,
                }
            )

        session_data = pending.pop(0)
        self.executor.plan.context[PLAN_CONTEXT_SAML_LOGOUT_REDIRECT_SESSIONS] = pending

        provider = SAMLProvider.objects.filter(pk=session_data.get("provider_pk")).first()
        if not provider:
            LOGGER.error(
                "Provider not found for logout",
                provider_pk=session_data.get("provider_pk"),
            )
            return self.get_challenge(*args, **kwargs)

        try:
            # Generate return URL back to this stage using the interface URL
            return_url = self.request.build_absolute_uri(
                reverse("authentik_core:if-flow", kwargs={"flow_slug": self.executor.flow.slug})
            )

            # Store return URL in session as fallback if SP doesn't echo RelayState
            # This is needed for SP-initiated logout views that are outside the flow context
            self.request.session[SESSION_KEY_SAML_LOGOUT_RETURN] = return_url

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

            if provider.sls_binding == SAMLBindings.POST:
                # For POST binding, return challenge with form data
                form_data = processor.get_post_form_data()
                return SAMLLogoutChallenge(
                    data={
                        "component": "ak-stage-saml-logout",
                        "url": provider.sls_url,
                        "saml_request": form_data["SAMLRequest"],
                        "relay_state": form_data["RelayState"],
                        "provider_name": provider.name,
                        "binding": SAMLBindings.POST,
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
                        "binding": SAMLBindings.REDIRECT,
                    }
                )
        except (KeyError, AttributeError) as exc:
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

        if challenge.initial_data.get("is_complete"):
            LOGGER.debug("All SAML providers logged out, completing stage")
            # Clean up the RelayState fallback
            self.request.session.pop(SESSION_KEY_SAML_LOGOUT_RETURN, None)
            return self.executor.stage_ok()

        # Otherwise, return the next challenge
        return HttpChallengeResponse(challenge)


class IframeLogoutChallenge(Challenge):
    """Challenge for iframe logout"""

    component = CharField(default="ak-stage-iframe-logout")
    logout_urls = ListField(child=DictField())


class IframeLogoutChallengeResponse(ChallengeResponse):
    """Response for iframe logout"""

    component = CharField(default="ak-stage-iframe-logout")


class IframeLogoutStageView(SAMLLogoutStageViewBase):
    """SAML and OIDC Logout stage that handles parallel iframe logout"""

    response_class = IframeLogoutChallengeResponse

    def _process_saml_session_for_logout(
        self, session_data: dict, user: User | None, return_url: str
    ) -> dict | None:
        """Process a single SAML session and return logout data"""
        provider = SAMLProvider.objects.filter(pk=session_data.get("provider_pk")).first()
        if not provider:
            LOGGER.warning(
                "SAML Provider not found for logout",
                provider_pk=session_data.get("provider_pk"),
            )
            return None

        try:
            processor = self._create_logout_processor(
                provider=provider,
                user=user,
                name_id=session_data["name_id"],
                name_id_format=session_data["name_id_format"],
                session_index=session_data.get("session_index", ""),
                relay_state=return_url,
            )

            if provider.sls_binding == SAMLBindings.POST:
                form_data = processor.get_post_form_data()
                return {
                    "url": provider.sls_url,
                    "saml_request": form_data["SAMLRequest"],
                    "provider_name": provider.name,
                    "binding": SAMLBindings.POST,
                    "relay_state": form_data["RelayState"],
                }
            else:
                logout_url = processor.get_redirect_url()
                return {
                    "url": logout_url,
                    "provider_name": provider.name,
                    "binding": SAMLBindings.REDIRECT,
                }
        except (KeyError, AttributeError) as exc:
            LOGGER.warning(
                "Failed to generate SAML logout URL",
                provider_pk=session_data.get("provider_pk"),
                exc=exc,
            )
            return None

    def _process_oidc_session_for_logout(self, session_data: dict, return_url: str) -> dict | None:
        """Process a single OIDC session and return logout data"""
        provider = OAuth2Provider.objects.filter(pk=session_data.get("provider_pk")).first()
        if not provider:
            LOGGER.warning(
                "OIDC Provider not found for logout",
                provider_pk=session_data.get("provider_pk"),
            )
            return None

        try:
            # Get ID token from session data
            id_token = session_data.get("id_token", {})

            # Build OIDC logout URL with required parameters
            params = {
                "id_token_hint": id_token.get("raw", ""),  # The raw JWT token
                "post_logout_redirect_uri": return_url,
                "state": session_data.get("session_id", ""),
            }

            # Remove empty parameters
            params = {k: v for k, v in params.items() if v}

            logout_url = f"{provider.frontchannel_logout_uri}?{urlencode(params)}"

            return {
                "url": logout_url,
                "provider_name": provider.name,
                "binding": "redirect",  # OIDC frontchannel is always via redirect/GET
                "provider_type": "oidc",
            }
        except (KeyError, AttributeError) as exc:
            LOGGER.warning(
                "Failed to generate OIDC logout URL",
                provider_pk=session_data.get("provider_pk"),
                exc=exc,
            )
            return None

    def get_challenge(self) -> Challenge:
        """Generate iframe logout challenge for both SAML and OIDC"""
        saml_sessions = self.executor.plan.context.get(PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS, [])
        oidc_sessions = self.executor.plan.context.get(PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS, [])

        return_url = self.request.build_absolute_uri(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.executor.flow.slug})
        )

        logout_urls = []

        # Process SAML sessions
        for session_data in saml_sessions:
            logout_data = self._process_saml_session_for_logout(
                session_data, user=None, return_url=return_url
            )
            if logout_data:
                logout_urls.append(logout_data)

        # Process OIDC sessions
        for session_data in oidc_sessions:
            logout_data = self._process_oidc_session_for_logout(session_data, return_url=return_url)
            if logout_data:
                logout_urls.append(logout_data)

        # Clear context after generating logout URLs
        self.executor.plan.context.pop(PLAN_CONTEXT_SAML_LOGOUT_IFRAME_SESSIONS, None)
        self.executor.plan.context.pop(PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS, None)

        LOGGER.debug(
            "Generated iframe logout challenge",
            saml_count=len(saml_sessions),
            oidc_count=len(oidc_sessions),
            total_urls=len(logout_urls),
        )

        return IframeLogoutChallenge(
            data={
                "component": "ak-stage-iframe-logout",
                "logout_urls": logout_urls,
            }
        )

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        """Iframe logout completed"""
        # Clean up the RelayState fallback
        self.request.session.pop(SESSION_KEY_SAML_LOGOUT_RETURN, None)
        return self.executor.stage_ok()
