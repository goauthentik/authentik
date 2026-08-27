from hmac import compare_digest
from re import error as RegexError
from re import fullmatch
from urllib.parse import urlparse

from django.http import HttpRequest
from django.urls import reverse
from guardian.shortcuts import get_anonymous_user
from sentry_sdk import start_span
from structlog.stdlib import BoundLogger, get_logger

from authentik.common.oauth.constants import (
    FORBIDDEN_URI_SCHEMES,
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    GRANT_TYPE_TOKEN_EXCHANGE,
)
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import (
    Application,
)
from authentik.events.models import Event, EventAction
from authentik.policies.engine import PolicyEngine
from authentik.providers.oauth2.dpop import DPoPError, DPoPValidator
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    ClientType,
    OAuth2Provider,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.utils import is_all_vschar, pkce_s256_challenge


class TokenRequest:

    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: str
    scope: set[str]

    code_verifier: str | None = None
    dpop_proof: str | None = None
    dpop_jwk: dict | None = None

    provider: OAuth2Provider
    audience_provider: OAuth2Provider | None = None
    logger: BoundLogger

    def __init__(self, provider: OAuth2Provider, client_id: str, client_secret: str):
        self.provider = provider
        self.logger = get_logger().bind(provider=provider.name)
        self.client_id = client_id
        self.client_secret = client_secret

    @property
    def token_provider(self) -> OAuth2Provider:
        """Provider the issued token is for: the `audience` target, else the client's own."""
        return self.audience_provider or self.provider

    def parse(self, request: HttpRequest) -> None:
        self.redirect_uri = request.POST.get("redirect_uri", "")
        self.grant_type = request.POST.get("grant_type", "")
        self.scope = set(request.POST.get("scope", "").split())
        # PKCE parameter.
        self.code_verifier = request.POST.get("code_verifier")
        # DPoP proof-of-possession header (RFC 9449)
        self.dpop_proof = request.headers.get("DPoP")
        # Token exchange parameter.
        self.requested_token_type = request.POST.get("requested_token_type")

        if self.grant_type not in self.provider.grant_types:
            self.logger.warning("Invalid grant_type for provider", grant_type=self.grant_type)
            raise TokenError("invalid_grant").with_cause("grant_type_not_configured")

        # Confidential clients MUST authenticate to the token endpoint per
        # RFC 6749 §2.3.1. The device code grant (RFC 8628 §3.4) and the token
        # exchange grant (RFC 8693 §2.1) inherit that requirement - neither the
        # device_code nor the subject_token is a substitute for client credentials.
        if self.grant_type in [
            GRANT_TYPE_AUTHORIZATION_CODE,
            GRANT_TYPE_REFRESH_TOKEN,
            GRANT_TYPE_DEVICE_CODE,
            GRANT_TYPE_TOKEN_EXCHANGE,
        ]:
            if self.provider.client_type == ClientType.CONFIDENTIAL and (
                not is_all_vschar(self.client_secret)
                or not compare_digest(self.provider.client_secret, self.client_secret)
            ):
                self.logger.warning(
                    "Invalid client secret",
                    client_id=self.provider.client_id,
                )
                raise TokenError("invalid_client").with_cause("invalid_secret")
        # Resolved before scopes, so they're clamped to the target provider's mappings
        self.resolve_audience(request)
        self.check_scopes()

    def resolve_audience(self, request: HttpRequest) -> None:
        """Resolve the provider the issued token is for. Only token exchange supports
        targeting a provider other than the client's own."""

    def check_scopes(self):
        allowed_scope_names = set(
            ScopeMapping.objects.filter(provider__in=[self.token_provider]).values_list(
                "scope_name", flat=True
            )
        )
        scopes_to_check = self.scope
        if not scopes_to_check.issubset(allowed_scope_names):
            self.logger.info(
                "Application requested scopes not configured, setting to overlap",
                scope_allowed=allowed_scope_names,
                scope_given=self.scope,
            )
            self.scope = self.scope.intersection(allowed_scope_names)

    def check_policy_access(self, app: Application, request: HttpRequest, **kwargs):
        with start_span(
            op="authentik.providers.oauth2.token.policy",
        ):
            user = self.user if self.user else get_anonymous_user()
            engine = PolicyEngine(app, user, request)
            engine.empty_result = AppAccessWithoutBindings.get()
            # Don't cache as for client_credentials flows the user will not be set
            # so we'll get generic cache results
            engine.use_cache = False
            engine.request.context["oauth_scopes"] = self.scope
            engine.request.context["oauth_grant_type"] = self.grant_type
            engine.request.context["oauth_code_verifier"] = self.code_verifier
            engine.request.context.update(kwargs)
            engine.build()
            result = engine.result
            if not result.passing:
                self.logger.info(
                    "User not authenticated for application", user=self.user, app_slug=app.slug
                )
                raise TokenError("invalid_grant")

    def validate_dpop(
        self,
        request: HttpRequest,
        dpop_jkt: str | None,
        raw_code: str | None = None,
        flow_name: str = "token",
    ) -> None:
        """Validate DPoP proof for key-bound tokens.

        :param request: The current HTTP request
        :param dpop_jkt: The expected JWK thumbprint (from auth request or previous token)
        :param raw_code: The raw authorization code or device code (for c_s256 computation)
        :param flow_name: Description of flow for logging (e.g., "authorization code")
        :raises TokenError: If DPoP validation fails
        """
        if not self.dpop_proof:
            self.logger.warning("Missing DPoP proof for key-bound token", flow_name=flow_name)
            raise TokenError("invalid_request")
        if dpop_jkt is None:
            self.logger.warning("bound_key scope requested but no dpop_jkt", flow_name=flow_name)
            raise TokenError("invalid_request")
        try:
            kwargs = {}
            if raw_code is not None:
                kwargs["expected_c_s256"] = pkce_s256_challenge(raw_code)
            token_url = request.build_absolute_uri(reverse("authentik_providers_oauth2:token"))
            self.dpop_jwk = DPoPValidator().validate(
                self.dpop_proof,
                expected_htm="POST",
                expected_htu=token_url,
                expected_jkt=dpop_jkt,
                **kwargs,
            )
        except DPoPError as exc:
            self.logger.warning("DPoP validation failed", flow_name=flow_name, exc=str(exc))
            raise TokenError("invalid_request") from exc

    def check_redirect_uri(self, request: HttpRequest):
        allowed_redirect_urls = self.provider.authorization_redirect_uris
        # At this point, no provider should have a blank redirect_uri, in case they do
        # this will check an empty array and raise an error

        match_found = False
        for allowed in allowed_redirect_urls:
            if allowed.matching_mode == RedirectURIMatchingMode.STRICT:
                if self.redirect_uri == allowed.url:
                    match_found = True
                    break
            if allowed.matching_mode == RedirectURIMatchingMode.REGEX:
                try:
                    if fullmatch(allowed.url, self.redirect_uri):
                        match_found = True
                        break
                except RegexError as exc:
                    self.logger.warning(
                        "Failed to parse regular expression",
                        exc=exc,
                        url=allowed.url,
                        provider=self.provider,
                    )
                    Event.new(
                        EventAction.CONFIGURATION_ERROR,
                        message="Invalid redirect_uri configured",
                        provider=self.provider,
                    ).from_http(request)
        if not match_found:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message="Invalid redirect URI used by provider",
                provider=self.provider,
                redirect_uri=self.redirect_uri,
                expected=allowed_redirect_urls,
            ).from_http(request)
            raise TokenError("invalid_client")

        # Check against forbidden schemes
        if urlparse(self.redirect_uri).scheme in FORBIDDEN_URI_SCHEMES:
            raise TokenError("invalid_request")
