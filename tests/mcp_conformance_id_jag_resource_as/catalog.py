"""Check catalog for authentik as an ID-JAG Resource Authorization Server.

Every ID listed must run exactly once and PASS (see checks.Report.verdict in the issuer
suite, which this suite shares). Spec: draft-ietf-oauth-identity-assertion-authz-grant-06.
"""

from tests.mcp_conformance_id_jag_issuer.checks import CheckDef, D

SUITE = "id-jag-resource-as"

CATALOG: tuple[CheckDef, ...] = (
    # --- configuration and discovery
    CheckDef(
        "ras.config.trust-idp",
        "An administrator trusts an IdP Authorization Server through the admin API: an "
        "OpenID Connect source created from the IdP's metadata URL (authentik fetches its "
        "JWKS), attached to a provider that enables the jwt-bearer grant",
        (f"{D}4.4.1 (trusted issuer)", f"{D}7.1"),
    ),
    CheckDef(
        "ras.discovery.metadata",
        "authentik's metadata, found from its issuer identifier, has the identical issuer, "
        "lists jwt-bearer in grant_types_supported and the ID-JAG profile in "
        "authorization_grant_profiles_supported",
        (f"{D}7.2", "RFC 8414 §3.3"),
    ),
    # --- positive control
    CheckDef(
        "ras.redeem",
        "An ID-JAG from the trusted IdP, presented with client_secret_basic, yields 200 with "
        "a Bearer access token, Cache-Control: no-store, and the granted scope",
        (f"{D}4.4, 4.4.1, 4.4.2", "RFC 7523 §2.1", "RFC 6749 §5.1"),
        upstream="complete-flow-jwt-bearer",
    ),
    CheckDef(
        "ras.access-token",
        "The access token verifies against authentik's JWKS (independent verifier), is "
        "issued by authentik for the redeeming client, names the user connected to the ID-JAG "
        "subject, and is accepted by authentik's userinfo endpoint",
        (f"{D}4.4.2, 5.2", "RFC 6750"),
    ),
    CheckDef(
        "ras.scope-semantics",
        "Granted scopes are a subset of the ID-JAG scope claim and are always reported",
        (f"{D}4.4.1 (scope)", "RFC 6749 §3.3, §5.1"),
    ),
    CheckDef(
        "ras.resource-bound",
        "An ID-JAG whose resource claim names a protected resource authentik governs yields "
        "an access token restricted (audience) to that resource",
        (f"{D}4.4.1 (resource)", "RFC 8707 §2"),
    ),
    CheckDef(
        "ras.e2e.authentik-issuer",
        "An ID-JAG issued by authentik (token exchange, as IdP Authorization Server) is "
        "redeemed by authentik as Resource Authorization Server for the same user",
        (f"{D}4.3, 4.4",),
    ),
    # --- negatives (§4.4.1 MUST reject with invalid_grant unless noted)
    CheckDef("ras.neg.typ", "typ other than oauth-id-jag+jwt is rejected", (f"{D}4.4.1",)),
    CheckDef(
        "ras.neg.alg-none",
        "An unsigned (alg none) ID-JAG is rejected",
        (f"{D}4.4.1", "RFC 8725 §3.1"),
    ),
    CheckDef(
        "ras.neg.signature",
        "An ID-JAG signed by another key under the trusted kid is rejected",
        (f"{D}4.4.1", "RFC 7521 §5.2"),
    ),
    CheckDef(
        "ras.neg.untrusted-issuer",
        "An ID-JAG naming an issuer authentik doesn't trust is rejected, even when signed by a "
        "trusted issuer's key",
        (f"{D}4.4.1 (iss)",),
    ),
    CheckDef(
        "ras.neg.audience",
        "An ID-JAG for another Resource Authorization Server is rejected",
        (f"{D}4.4.1 (aud)",),
    ),
    CheckDef(
        "ras.neg.audience-array",
        "An aud array with more than one element is rejected",
        (f"{D}4.4.1 (aud array has exactly one element)",),
    ),
    CheckDef(
        "ras.neg.client-binding",
        "An ID-JAG for another client is rejected when presented by this client",
        (f"{D}4.4.1 (client_id)",),
    ),
    CheckDef(
        "ras.neg.expired",
        "An expired ID-JAG is rejected",
        (f"{D}4.4.1", "RFC 7523 §3"),
    ),
    CheckDef(
        "ras.neg.missing-claim",
        "An ID-JAG without jti is rejected",
        (f"{D}3.1 (jti REQUIRED)",),
    ),
    CheckDef(
        "ras.neg.replay",
        "A redeemed ID-JAG is not accepted again",
        (f"{D}4.4.4", "RFC 7523 §3"),
    ),
    CheckDef(
        "ras.neg.resource-not-governed",
        "An ID-JAG for a resource authentik doesn't govern is rejected",
        (f"{D}4.4.1 (resource)",),
    ),
    CheckDef(
        "ras.neg.no-client-auth",
        "A request without client authentication is rejected with invalid_client",
        (f"{D}4.4 (MUST invalid_client)",),
    ),
    CheckDef(
        "ras.neg.subject-not-provisioned",
        "A valid ID-JAG for a subject with no account here is refused with access_denied",
        (f"{D}4.4.3 (access_denied)",),
    ),
)
