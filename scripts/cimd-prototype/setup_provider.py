"""PROTOTYPE (01b), never merge: create the CIMD-enabled provider and application.

    uv run manage.py shell -c "exec(open('scripts/cimd-prototype/setup_provider.py').read())"

Idempotent. Prints the issuer and client_id for mcp_server.py.
"""

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import (
    ClientType,
    GrantType,
    IssuerMode,
    OAuth2Provider,
    ScopeMapping,
)

SLUG = "mcp-proto"

provider, _ = OAuth2Provider.objects.update_or_create(
    name="CIMD prototype (MCP)",
    defaults={
        "client_type": ClientType.PUBLIC,
        "authorization_flow": Flow.objects.get(
            slug="default-provider-authorization-explicit-consent"
        ),
        "invalidation_flow": Flow.objects.get(slug="default-provider-invalidation-flow"),
        "signing_key": CertificateKeyPair.objects.get(name="authentik Self-signed Certificate"),
        "issuer_mode": IssuerMode.PER_PROVIDER,
        "grant_types": [GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
        # Short enough that clients refresh during a session, but longer than the
        # ~5 minute pre-expiry refresh margin MCP clients appear to use; at 5 minutes,
        # Claude Code refreshed before every request and VS Code refreshed in a loop
        "access_token_validity": "minutes=10",
        "refresh_token_validity": "days=7",
        "refresh_token_threshold": "seconds=0",
        "_redirect_uris": [],
    },
)
provider.property_mappings.set(
    ScopeMapping.objects.filter(
        managed__in=[
            "goauthentik.io/providers/oauth2/scope-openid",
            "goauthentik.io/providers/oauth2/scope-email",
            "goauthentik.io/providers/oauth2/scope-profile",
            "goauthentik.io/providers/oauth2/scope-offline_access",
        ]
    )
)
Application.objects.update_or_create(
    slug=SLUG, defaults={"name": "CIMD prototype (MCP)", "provider": provider}
)
print(f"issuer:    http://localhost:9000/application/o/{SLUG}/")
print(f"client_id: {provider.client_id}")
