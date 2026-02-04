"""oauth2 provider end_session Views"""

from re import fullmatch
from urllib.parse import quote

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from authentik.common.oauth.constants import PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS
from authentik.core.models import Application, AuthenticatedSession
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_POST_LOGOUT_REDIRECT_URI,
    FlowPlanner,
)
from authentik.flows.stage import SessionEndStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.policies.views import PolicyAccessView
from authentik.providers.iframe_logout import IframeLogoutStageView
from authentik.providers.oauth2.models import (
    AccessToken,
    OAuth2LogoutMethod,
    RedirectURIMatchingMode,
)
from authentik.providers.oauth2.tasks import send_backchannel_logout_request
from authentik.providers.oauth2.utils import build_frontchannel_logout_url


class EndSessionView(PolicyAccessView):
    """OIDC RP-Initiated Logout endpoint"""

    flow: Flow
    post_logout_redirect_uri: str | None

    def resolve_provider_application(self):
        self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
        self.provider = self.application.get_provider()
        if not self.provider:
            raise Http404
        self.flow = self.provider.invalidation_flow or self.request.brand.flow_invalidation
        if not self.flow:
            raise Http404

        # Parse end session parameters
        query_dict = self.request.POST if self.request.method == "POST" else self.request.GET
        state = query_dict.get("state")
        request_redirect_uri = query_dict.get("post_logout_redirect_uri")
        self.post_logout_redirect_uri = None

        # Validate post_logout_redirect_uri against registered URIs
        if request_redirect_uri:
            for allowed in self.provider.post_logout_redirect_uris:
                if allowed.matching_mode == RedirectURIMatchingMode.STRICT:
                    if request_redirect_uri == allowed.url:
                        self.post_logout_redirect_uri = request_redirect_uri
                        break
                elif allowed.matching_mode == RedirectURIMatchingMode.REGEX:
                    if fullmatch(allowed.url, request_redirect_uri):
                        self.post_logout_redirect_uri = request_redirect_uri
                        break

        # Append state to the redirect URI if both are present
        if self.post_logout_redirect_uri and state:
            separator = "&" if "?" in self.post_logout_redirect_uri else "?"
            self.post_logout_redirect_uri = (
                f"{self.post_logout_redirect_uri}{separator}state={quote(state, safe='')}"
            )

    # If IFrame provider logout happens when a saml provider has redirect
    # logout enabled, the flow won't make it back without this dispatch
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check for active logout flow before policy checks"""

        # Check if we're already in an active logout flow
        # (being called from an iframe during single logout)
        if SESSION_KEY_PLAN in request.session:
            return HttpResponse(
                "<html><body>Logout successful</body></html>", content_type="text/html", status=200
            )

        # Otherwise, continue with normal policy checks
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the flow planner for the invalidation flow"""
        planner = FlowPlanner(self.flow)
        planner.allow_empty_flows = True

        # Build flow context with logout parameters
        context = {
            PLAN_CONTEXT_APPLICATION: self.application,
        }

        # Add validated redirect URI (with state appended) to context if available
        if self.post_logout_redirect_uri:
            context[PLAN_CONTEXT_POST_LOGOUT_REDIRECT_URI] = self.post_logout_redirect_uri

        # Get session info for logout notifications
        auth_session = AuthenticatedSession.from_request(request, request.user)
        session_key = (
            auth_session.session.session_key if auth_session and auth_session.session else None
        )

        # Handle frontchannel logout
        frontchannel_logout_url = None
        if self.provider.logout_method == OAuth2LogoutMethod.FRONTCHANNEL:
            frontchannel_logout_url = build_frontchannel_logout_url(
                self.provider, request, session_key
            )

        # Handle backchannel logout
        if (
            self.provider.logout_method == OAuth2LogoutMethod.BACKCHANNEL
            and self.provider.logout_uri
        ):
            # Find access token to get iss and sub for the logout token
            access_token = AccessToken.objects.filter(
                user=request.user,
                provider=self.provider,
                session=auth_session,
            ).first()
            if access_token and access_token.id_token:
                send_backchannel_logout_request.send(
                    self.provider.pk,
                    access_token.id_token.iss,
                    access_token.id_token.sub,
                    session_key,
                )
                # Delete the token to prevent duplicate backchannel logout
                # when UserLogoutStage triggers the session deletion signal
                access_token.delete()

        if frontchannel_logout_url:
            context[PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS] = [
                {
                    "url": frontchannel_logout_url,
                    "provider_name": self.provider.name,
                    "binding": "redirect",
                    "provider_type": "oidc",
                }
            ]

        plan = planner.plan(request, context)

        # Inject iframe logout stage if frontchannel logout is configured
        if frontchannel_logout_url:
            plan.insert_stage(in_memory_stage(IframeLogoutStageView))

        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(self.request, self.flow)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle POST requests for logout (same as GET per OIDC spec)"""
        return self.get(request, *args, **kwargs)
