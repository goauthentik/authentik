"""oauth2 provider end_session Views"""

from re import fullmatch
from urllib.parse import quote, urlparse

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from jwt import PyJWTError
from jwt import decode as jwt_decode

from authentik.common.oauth.constants import (
    FORBIDDEN_URI_SCHEMES,
    OAUTH2_BINDING,
    PLAN_CONTEXT_OIDC_LOGOUT_IFRAME_SESSIONS,
    PLAN_CONTEXT_POST_LOGOUT_REDIRECT_URI,
)
from authentik.core.models import Application, AuthenticatedSession
from authentik.flows.models import Flow, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    FlowPlanner,
)
from authentik.flows.stage import SessionEndStage
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView
from authentik.providers.iframe_logout import IframeLogoutStageView
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    AccessToken,
    JWTAlgorithms,
    OAuth2LogoutMethod,
    OAuth2Provider,
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

    def validate(self):
        # Parse end session parameters
        query_dict = self.request.POST if self.request.method == "POST" else self.request.GET
        state = query_dict.get("state")
        request_redirect_uri = query_dict.get("post_logout_redirect_uri")
        id_token_hint = query_dict.get("id_token_hint")
        self.post_logout_redirect_uri = None

        # OIDC Certification: Verify id_token_hint. If invalid or missing, throw an error
        if id_token_hint:
            # Load a fresh provider instance that's not part of the flow
            # since it'll have the cryptography Certificate that can't be pickled
            provider = OAuth2Provider.objects.get(pk=self.provider.pk)
            key, alg = provider.jwt_key
            if alg != JWTAlgorithms.HS256:
                key = provider.signing_key.public_key
            try:
                jwt_decode(
                    id_token_hint,
                    key,
                    algorithms=[alg],
                    audience=provider.client_id,
                    issuer=provider.get_issuer(self.request),
                    # ID Tokens are short-lived; a logout request arriving
                    # after expiry is still legitimate and must succeed.
                    options={"verify_exp": False},
                )
            except PyJWTError:
                raise TokenError("invalid_request").with_cause(
                    "id_token_hint_decode_failed"
                ) from None

        # Validate post_logout_redirect_uri against registered URIs
        if request_redirect_uri:
            # OIDC Certification: id_token_hint required with post_logout_redirect_uri
            if not id_token_hint:
                raise TokenError("invalid_request").with_cause("id_token_hint_missing")
            if urlparse(request_redirect_uri).scheme in FORBIDDEN_URI_SCHEMES:
                raise TokenError("invalid_request").with_cause("post_logout_redirect_uri")
            for allowed in self.provider.post_logout_redirect_uris:
                if allowed.matching_mode == RedirectURIMatchingMode.STRICT:
                    if request_redirect_uri == allowed.url:
                        self.post_logout_redirect_uri = request_redirect_uri
                        break
                elif allowed.matching_mode == RedirectURIMatchingMode.REGEX:
                    if fullmatch(allowed.url, request_redirect_uri):
                        self.post_logout_redirect_uri = request_redirect_uri
                        break
            # OIDC Certification: OP MUST NOT perform post-logout redirection
            # if the supplied URI does not exactly match a registered one
            if self.post_logout_redirect_uri is None:
                raise TokenError("invalid_request").with_cause("invalid_post_logout_redirect_uri")

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

        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the flow planner for the invalidation flow"""
        try:
            self.validate()
        except TokenError as exc:
            return bad_request_message(
                self.request,
                exc.description,
            )
        planner = FlowPlanner(self.flow)
        planner.allow_empty_flows = True

        context = {
            PLAN_CONTEXT_APPLICATION: self.application,
        }

        auth_session = AuthenticatedSession.from_request(request, request.user)

        if self.post_logout_redirect_uri:
            context[PLAN_CONTEXT_POST_LOGOUT_REDIRECT_URI] = self.post_logout_redirect_uri

        session_key = (
            auth_session.session.session_key if auth_session and auth_session.session else None
        )

        frontchannel_logout_url = None
        if self.provider.logout_method == OAuth2LogoutMethod.FRONTCHANNEL:
            frontchannel_logout_url = build_frontchannel_logout_url(
                self.provider, request, session_key
            )

        if (
            self.provider.logout_method == OAuth2LogoutMethod.BACKCHANNEL
            and self.provider.logout_uri
        ):
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
                    "binding": OAUTH2_BINDING,
                    "provider_type": (
                        f"{self.provider._meta.app_label}.{self.provider._meta.model_name}"
                    ),
                }
            ]

        access_tokens = AccessToken.objects.filter(
            user=request.user,
            provider=self.provider,
        )
        if auth_session:
            access_tokens = access_tokens.filter(session=auth_session)
        access_tokens.delete()

        plan = planner.plan(request, context)

        if frontchannel_logout_url:
            plan.insert_stage(in_memory_stage(IframeLogoutStageView))

        plan.append_stage(in_memory_stage(SessionEndStage))
        return plan.to_redirect(self.request, self.flow)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle POST requests for logout (same as GET per OIDC spec)"""
        return self.get(request, *args, **kwargs)
