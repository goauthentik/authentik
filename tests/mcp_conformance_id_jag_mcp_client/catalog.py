"""Check catalog for the ID-JAG end-to-end suite driven by the official MCP TypeScript SDK.

authentik plays both roles: IdP Authorization Server (issues ID-JAGs by token exchange) and
the MCP server's Resource Authorization Server (redeems them with jwt-bearer). Every ID listed
must run exactly once and PASS (checks.Report.verdict in the issuer suite, which this suite
shares). Spec: draft-ietf-oauth-identity-assertion-authz-grant-06, MCP Enterprise-Managed
Authorization (SEP-990).
"""

from tests.mcp_conformance_id_jag_issuer.checks import CheckDef, D

SUITE = "id-jag-mcp-client"
MCP_AUTH = "MCP 2025-11-25 Authorization"
MCP_EMA = "MCP Enterprise-Managed Authorization"

CATALOG: tuple[CheckDef, ...] = (
    # --- configuration
    CheckDef(
        "config.authentik-both-roles",
        "An administrator configures authentik in both roles through the admin API: the "
        "Resource AS provider trusts the IdP provider (OpenID Connect source from its metadata "
        "URL, jwt-bearer grant), and a system agent links the MCP client's application to the "
        "Resource AS audience, client ID and MCP resource",
        (f"{D}4.3.3, 4.4.1, 5.1",),
    ),
    # --- discovery (SDK)
    CheckDef(
        "mcp.discovery",
        "The SDK discovers the MCP server's authorization server: 401 with resource_metadata, "
        "Protected Resource Metadata naming the authentik Resource AS, its metadata with the "
        "identical issuer, jwt-bearer and the ID-JAG grant profile",
        ("RFC 9728 §3.3, §5.1", "RFC 8414 §3.3", f"{D}7.2", MCP_AUTH),
    ),
    # --- step 1
    CheckDef(
        "sso.id-token",
        "openid-client signs the user in at authentik (authorization code + PKCE) and verifies "
        "the ID token (signature, iss, aud, nonce)",
        ("OIDC Core 1.0 §3.1.3.7", f"{D}4.2"),
    ),
    # --- step 2
    CheckDef(
        "exchange.id-jag",
        "The SDK's discoverAndRequestJwtAuthGrant exchanges the ID token at authentik for an "
        "ID-JAG for the Resource AS and the MCP resource; the ID-JAG verifies against "
        "authentik's JWKS and binds aud, client_id, sub and resource",
        (f"{D}3.1, 4.3, 4.3.3, 4.3.4", "RFC 8693 §2", MCP_EMA),
        upstream="complete-flow-token-exchange",
    ),
    CheckDef(
        "exchange.scope-forwarding",
        "A scope forwarded by the SDK's documented assertion callback is either granted "
        "consistently or refused explicitly with invalid_scope, never silently dropped",
        (f"{D}4.3 (scope), 4.3.4", "RFC 8693 §2.2.1, §2.2.2"),
    ),
    # --- step 3
    CheckDef(
        "redeem.resource-bound",
        "The SDK's exchangeJwtAuthGrant redeems the resource-bound ID-JAG it requested at "
        "authentik's Resource AS",
        (f"{D}4.4.1 (resource)", "RFC 8707 §2"),
    ),
    CheckDef(
        "redeem.id-jag",
        "The SDK's CrossAppAccessProvider redeems an ID-JAG at authentik's Resource AS with "
        "jwt-bearer, during Client.connect, and receives a Bearer access token",
        (f"{D}4.4, 4.4.1, 4.4.2", "RFC 7523 §2.1", MCP_EMA),
        upstream="complete-flow-jwt-bearer",
    ),
    CheckDef(
        "redeem.client-auth-methods",
        "authentik accepts the SDK's jwt-bearer request with client_secret_basic (the SDK "
        "default) and client_secret_post (the override used in Okta's sample)",
        (f"{D}4.4", "RFC 6749 §2.3.1"),
    ),
    # --- step 4
    CheckDef(
        "mcp.tool-call",
        "The SDK's Client and StreamableHTTPClientTransport call the MCP server with the "
        "access token (initialize, tools/call); the server verifies it against the Resource "
        "AS and sees the signed-in user",
        (MCP_AUTH, MCP_EMA, "RFC 6750 §2.1"),
    ),
    CheckDef(
        "mcp.audience-bound",
        "A spec-compliant MCP server that only accepts tokens issued for its resource "
        "(token audience binding) accepts the access token",
        (f"{MCP_AUTH} (token audience binding)", "RFC 8707 §2"),
    ),
    CheckDef(
        "e2e.sdk-default",
        "The SDK's documented Cross-App Access flow, unmodified (CrossAppAccessProvider with "
        "discoverAndRequestJwtAuthGrant), reaches a spec-compliant MCP server",
        (MCP_EMA, f"{D}4.3, 4.4"),
    ),
    # --- negatives (gated on the positive controls)
    CheckDef(
        "neg.exchange.wrong-audience",
        "Token exchange for an audience with no trust relationship is rejected with "
        "invalid_target",
        (f"{D}4.3.3 (MUST invalid_target)",),
    ),
    CheckDef(
        "neg.exchange.unregistered-resource",
        "Token exchange for a resource not registered for the audience is rejected with "
        "invalid_target",
        (f"{D}4.3.3 (MUST invalid_target when none granted)",),
    ),
    CheckDef(
        "neg.exchange.unlinked-app",
        "Token exchange by an application the agent isn't linked to is refused "
        "(access_denied per the -06 profile, invalid_target per RFC 8693 §2.2.2)",
        (f"{D}4.3.3, 4.3.4.3", "RFC 8693 §2.2.2"),
    ),
    CheckDef(
        "neg.redeem.replay",
        "An ID-JAG the SDK already redeemed is refused with invalid_grant when presented again",
        (f"{D}4.4.4", "RFC 7523 §3"),
    ),
)
