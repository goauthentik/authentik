from dataclasses import dataclass, field
from typing import Any

from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from jwt import PyJWK, PyJWT, PyJWTError, decode

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
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.models import (
    AccessToken,
    OAuth2Provider,
)
from authentik.providers.oauth2.token.base import TokenRequest
from authentik.sources.oauth.models import OAuthSource


@dataclass(frozen=True)
class FederatedParty:
    """Details about a _verified_ federation party"""

    parsed_token: dict[str, Any]
    party: OAuth2Provider | OAuthSource
    user: User | None = field(default=None)

    @property
    def type(self) -> str:
        if isinstance(self.party, OAuth2Provider):
            return "provider"
        if isinstance(self.party, OAuthSource):
            return "source"
        raise ValueError(f"Invalid party type {self.party}")


class FederatedTokenRequest(TokenRequest):
    """Base class for token requests which involve federation, such as
    client_credentials or token exchange"""

    # Set by the grants that resolve an identity; read by check_policy_access and the
    # response builders, so it must exist on every request type.
    user: User | None = None
    actor: Actor | None = None
    requested_token_type: str | None = None

    def validate_jwt(self, assertion: str) -> FederatedParty | None:
        if party := self.validate_jwt_from_source(assertion):
            return party
        elif party := self.validate_jwt_from_provider(assertion):
            return party
        return None

    def validate_jwt_from_source(self, assertion: str) -> FederatedParty | None:
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
            return None
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
                return FederatedParty(parsed_token=token, party=source)
        return None

    def validate_jwt_from_provider(self, assertion: str) -> FederatedParty | None:
        token = provider = resolved_user = _key = None
        providers = Q(provider__in=self.provider.jwt_federation_providers.all())
        if self.audience_provider:
            # For token exchange with actor, the given token may likely be a token
            # of the provider this request is for
            providers |= Q(provider=self.provider)
        federated_token = AccessToken.objects.filter(providers, token=assertion).first()
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

        if not token:
            return None
        self.logger.info("successfully verified JWT with provider", provider=provider.name)
        return FederatedParty(parsed_token=token, party=provider, user=resolved_user)

    def create_user_from_jwt(
        self, party: FederatedParty, app: Application, request: HttpRequest
    ) -> User:
        """Create user from JWT"""
        if not isinstance(party.party, OAuthSource):
            raise ValueError("create_user_from_jwt can only be called with source as party")
        with audit_ignore():
            # Run the JWT payload through the core mapping engine
            mapped = SourceMapper(party.party).build_object_properties(
                User, request=request, info=party.parsed_token, oauth_userinfo=party.parsed_token
            )

            user, created = User.objects.update_or_create(
                username=mapped.get(
                    "username", f"{self.provider.name}-{party.parsed_token.get('sub')}"
                )[:USERNAME_MAX_LENGTH],
                defaults={
                    "last_login": timezone.now(),
                    "name": mapped.get(
                        "name",
                        f"Autogenerated user from application {app.name} (client credentials JWT)",
                    ),
                    "email": mapped.get("email", ""),
                    "path": party.party.get_user_path(),
                    "type": UserTypes.SERVICE_ACCOUNT,
                    "attributes": mapped.get("attributes", {}),
                },
            )
            user.attributes[USER_ATTRIBUTE_GENERATED] = True
            user.save()
            exp = party.parsed_token.get("exp")
            if created and exp:
                user.attributes[USER_ATTRIBUTE_EXPIRES] = exp
                user.save()
            return user
