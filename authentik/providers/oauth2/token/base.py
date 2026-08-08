from hmac import compare_digest
from re import error as RegexError
from re import fullmatch
from typing import Any
from urllib.parse import urlparse

from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import get_anonymous_user
from jwt import PyJWK, PyJWT, PyJWTError, decode
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
    USER_ATTRIBUTE_EXPIRES,
    USER_ATTRIBUTE_GENERATED,
    USERNAME_MAX_LENGTH,
    Actor,
    Application,
    User,
    UserTypes,
)
from authentik.core.sources.mapper import SourceMapper
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.policies.engine import PolicyEngine
from authentik.providers.oauth2.dpop import DPoPError, DPoPValidator
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    OAuth2Provider,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.utils import is_all_vschar, pkce_s256_challenge
from authentik.sources.oauth.models import OAuthSource


class TokenRequest:

    client_id: str
    client_secret: str
    redirect_uri: str
    grant_type: str
    scope: set[str]

    code_verifier: str | None = None
    dpop_proof: str | None = None
    dpop_jwk: dict | None = None
    # Set by the grants that resolve an identity; read by check_policy_access and the
    # response builders, so it must exist on every request type.
    user: User | None = None
    actor: Actor | None = None
    requested_token_type: str | None = None

    provider: OAuth2Provider
    logger: BoundLogger

    def __init__(self, provider: OAuth2Provider, client_id: str, client_secret: str):
        self.provider = provider
        self.logger = get_logger().bind(provider=provider.name)
        self.client_id = client_id
        self.client_secret = client_secret

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
        self.check_scopes()

    def check_scopes(self):
        allowed_scope_names = set(
            ScopeMapping.objects.filter(provider__in=[self.provider]).values_list(
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

    def validate_jwt_from_source(
        self, assertion: str
    ) -> tuple[dict, OAuthSource] | tuple[None, None]:
        # Fully decode the JWT without verifying the signature, so we can get access to
        # the header.
        # Get the Key ID from the header, and use that to optimize our source query to only find
        # sources that have a JWK for that Key ID
        # The Key ID doesn't have a fixed format, but must match between an issued JWT
        # and whatever is returned by the JWKS endpoint
        try:
            decode_unvalidated = PyJWT().decode_complete(
                assertion, options={"verify_signature": False}
            )
        except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
            self.logger.warning("failed to parse JWT for kid lookup", exc=exc)
            raise TokenError("invalid_grant") from None
        expected_kid = decode_unvalidated["header"].get("kid")
        fallback_alg = decode_unvalidated["header"].get("alg")
        if not expected_kid or not fallback_alg:
            return None, None
        for source in self.provider.jwt_federation_sources.filter(
            oidc_jwks__keys__contains=[{"kid": expected_kid}]
        ):
            self.logger.debug("verifying JWT with source", source=source.slug)
            keys = source.oidc_jwks.get("keys", [])
            for key in keys:
                if key.get("kid") and key.get("kid") != expected_kid:
                    continue
                self.logger.debug("verifying JWT with key", source=source.slug, key=key.get("kid"))
                try:
                    parsed_key = PyJWK.from_dict(key).key
                    token = decode(
                        assertion,
                        parsed_key,
                        algorithms=[key.get("alg")] if "alg" in key else [fallback_alg],
                        options={
                            "verify_aud": False,
                        },
                    )
                # AttributeError is raised when the configured JWK is a private key
                # and not a public key
                except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
                    self.logger.warning("failed to verify JWT", exc=exc, source=source.slug)
                    continue
                # Return on the first key that verifies, so the source reported back is the
                # one that actually validated the JWT rather than the last one iterated.
                # The caller feeds this source into create_user_from_jwt, where it selects
                # the user path and property mappings.
                self.logger.info("successfully verified JWT with source", source=source.slug)
                return token, source
        return None, None

    def validate_jwt_from_provider(
        self, assertion: str
    ) -> tuple[dict, OAuth2Provider, User] | tuple[None, None, None]:
        token = provider = resolved_user = _key = None
        federated_token = AccessToken.objects.filter(
            token=assertion, provider__in=self.provider.jwt_federation_providers.all()
        ).first()
        if federated_token:
            _key, _alg = federated_token.provider.jwt_key
            try:
                token = decode(
                    assertion,
                    _key.public_key(),
                    algorithms=[_alg],
                    options={
                        "verify_aud": False,
                    },
                )
                provider = federated_token.provider
                resolved_user = federated_token.user
            except (PyJWTError, ValueError, TypeError, AttributeError) as exc:
                self.logger.warning(
                    "failed to verify JWT", exc=exc, provider=federated_token.provider.name
                )

        if token:
            self.logger.info("successfully verified JWT with provider", provider=provider.name)
        return token, provider, resolved_user

    def create_user_from_jwt(
        self, token: dict[str, Any], app: Application, source: OAuthSource, request: HttpRequest
    ):
        """Create user from JWT"""
        with audit_ignore():
            # Run the JWT payload through the core mapping engine
            mapped = SourceMapper(source).build_object_properties(
                User, request=request, info=token, oauth_userinfo=token
            )

            self.user, created = User.objects.update_or_create(
                username=mapped.get("username", f"{self.provider.name}-{token.get('sub')}")[
                    :USERNAME_MAX_LENGTH
                ],
                defaults={
                    "last_login": timezone.now(),
                    "name": mapped.get(
                        "name",
                        f"Autogenerated user from application {app.name} (client credentials JWT)",
                    ),
                    "email": mapped.get("email", ""),
                    "path": source.get_user_path(),
                    "type": UserTypes.SERVICE_ACCOUNT,
                    "attributes": mapped.get("attributes", {}),
                },
            )
            self.user.attributes[USER_ATTRIBUTE_GENERATED] = True
            self.user.save()
            exp = token.get("exp")
            if created and exp:
                self.user.attributes[USER_ATTRIBUTE_EXPIRES] = exp
                self.user.save()
