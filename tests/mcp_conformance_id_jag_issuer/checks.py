"""Check catalog and structured report for the ID-JAG issuer acceptance check.

stdlib only. Every check the acceptance run must produce is listed in CATALOG; the run fails
unless *every* catalog ID is present exactly once with status PASS. Unknown IDs, missing IDs,
BLOCKED (a prerequisite failed, so a negative would be vacuous), FAIL and ERROR all fail.

Spec revision: draft-ietf-oauth-identity-assertion-authz-grant-06 (31 October 2026), see
README.md "Provenance" for the -04 vs -06 differences and the MCP / upstream mapping.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape, quoteattr  # nosec B406 - output escaping only, no parsing

DRAFT = "draft-ietf-oauth-identity-assertion-authz-grant-06"
D = f"{DRAFT} §"

PASS, FAIL, BLOCKED, ERROR = "PASS", "FAIL", "BLOCKED", "ERROR"


@dataclass(frozen=True)
class CheckDef:
    id: str
    title: str
    refs: tuple[str, ...]
    # Name of the upstream modelcontextprotocol/conformance check this corresponds to, if any
    upstream: str | None = None


CATALOG: tuple[CheckDef, ...] = (
    # --- capability / provisioning (authentik admin model, PR goauthentik/authentik#26973)
    CheckDef(
        "capability.agent-id-jag-config",
        "authentik exposes system-agent ID-JAG trust configuration (audience, client_id, "
        "resources, applications) so a Resource AS trust relationship can be provisioned",
        (f"{D}4.3.3 (trust relationship)", f"{D}5.1 (client ID mapping)"),
    ),
    # --- discovery
    CheckDef(
        "discovery.mcp-prm",
        "MCP resource returns 401 + resource_metadata; PRM resource/authorization_servers "
        "validated; Resource AS metadata issuer validated",
        ("RFC 9728 §3.3, §5.1", f"{D}9.5, 9.6", "RFC 8414 §3.3"),
    ),
    CheckDef(
        "discovery.idp-metadata",
        "authentik metadata reachable from its issuer identifier, issuer identical, "
        "token_endpoint and jwks_uri present",
        ("RFC 8414 §3.3", "OIDC Discovery 1.0 §4.3", f"{D}7.1"),
    ),
    # --- SSO
    CheckDef(
        "sso.id-token",
        "Real authentik login + authorization code (PKCE) flow yields an ID Token whose "
        "signature verifies against authentik's JWKS and whose aud is the client",
        ("OIDC Core 1.0 §3.1.3.7", f"{D}4.2"),
    ),
    # --- positive control
    CheckDef(
        "exchange.id-jag-issued",
        "Token exchange (subject_token_type=id_token, requested_token_type=id-jag, "
        "audience=Resource AS issuer, resource=MCP resource) returns 200 with "
        "issued_token_type=id-jag, token_type=N_A, access_token, Cache-Control: no-store",
        (f"{D}4.3, 4.3.4", "RFC 8693 §2.2.1", "RFC 6749 §5.1"),
        upstream="complete-flow-token-exchange",
    ),
    CheckDef(
        "assertion.jose",
        "ID-JAG header typ=oauth-id-jag+jwt, asymmetric alg, signature verified against "
        "authentik JWKS by the independent verifier",
        (f"{D}3, 3.1", "RFC 8725 §3.11", "RFC 7515"),
    ),
    CheckDef(
        "assertion.claims",
        "ID-JAG REQUIRED claims iss/sub/aud/client_id/jti/exp/iat present and bound: iss = "
        "authentik issuer, aud = Resource AS issuer, client_id = client's id AT the "
        "Resource AS, resource = requested resource exactly, sub = SSO subject",
        (f"{D}3.1, 4.3.3, 5.1", "RFC 7519 §4.1"),
    ),
    CheckDef(
        "assertion.not-a-bearer-token",
        "The ID-JAG is not accepted by authentik as a bearer access token (userinfo)",
        (f"{D}4.3.4 (token_type N_A)", "RFC 8693 §2.2.1"),
    ),
    CheckDef(
        "ras.redeem",
        "Independent Resource AS accepts the authentik ID-JAG via RFC 7523 jwt-bearer "
        "with client_secret_basic and issues a Bearer access token",
        (f"{D}4.4, 4.4.1, 4.4.2", "RFC 7523 §2.1, §3", "RFC 7521 §5.2"),
        upstream="complete-flow-jwt-bearer",
    ),
    CheckDef(
        "mcp.access",
        "Protected MCP resource accepts the Resource AS access token (initialize, "
        "tools/call whoami) and reports the ID-JAG subject",
        ("MCP 2025-11-25 Authorization", "MCP EMA 2026-07-28 'Access Token'"),
    ),
    CheckDef(
        "ras.client-binding",
        "Resource AS rejects the same authentik ID-JAG when presented by a different "
        "authenticated client (client_id binding is meaningful)",
        (f"{D}4.4.1",),
    ),
    # --- scope semantics (separate so the core flow is not masked)
    CheckDef(
        "exchange.scope-semantics",
        "A Resource-AS scope is either granted into the ID-JAG scope claim or the response "
        "states the granted scope; it is never silently dropped",
        (f"{D}4.3 (scope), 4.3.3, 4.3.4", "RFC 8693 §2.2.1"),
    ),
    # --- negatives at the authentik token endpoint
    CheckDef(
        "negative.wrong-client-id-token",
        "ID Token issued to another authentik client is rejected with invalid_request",
        (f"{D}4.3.3, 4.3.4.3", "RFC 8693 §2.2.2 (MUST invalid_request)"),
    ),
    CheckDef(
        "negative.tampered-id-token",
        "ID Token with a broken signature is rejected with invalid_request",
        (f"{D}4.3.3, 4.3.4.3", "RFC 8693 §2.2.2"),
    ),
    CheckDef(
        "negative.access-token-as-subject",
        "An authentik access token presented as subject_token_type=id_token is rejected",
        (f"{D}4.3.3 (MUST NOT accept other token purposes)", "RFC 8693 §2.2.2"),
    ),
    CheckDef(
        "negative.id-jag-as-subject",
        "An ID-JAG presented as subject_token_type=id_token is rejected",
        (f"{D}4.3.3 (MUST NOT accept other token purposes)", "RFC 8693 §2.2.2"),
    ),
    CheckDef(
        "negative.unknown-audience",
        "An audience with no trust relationship is rejected with invalid_target",
        (f"{D}4.3.3 (MUST invalid_target)",),
    ),
    CheckDef(
        "negative.multiple-audiences",
        "More than one audience is rejected with invalid_request",
        (f"{D}4.3.3 (MUST invalid_request)",),
    ),
    CheckDef(
        "negative.resource-not-governed",
        "A resource not governed by the audience is rejected with invalid_target",
        (f"{D}4.3.3 (MUST invalid_target when none granted)",),
    ),
    CheckDef(
        "negative.client-not-authorized-for-audience",
        "A trusted audience that this client is not authorized for is refused "
        "(access_denied per -06 profile, invalid_target accepted per RFC 8693 §2.2.2)",
        (f"{D}4.3.3, 4.3.4.3", "RFC 8693 §2.2.2"),
    ),
    CheckDef(
        "negative.no-client-auth",
        "Request without client authentication is rejected with invalid_client",
        (f"{D}4.3.3 (MUST invalid_client)", "RFC 6749 §5.2"),
    ),
)

CATALOG_IDS = tuple(c.id for c in CATALOG)


@dataclass
class CheckResult:
    id: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    duration_s: float = 0.0


class Report:
    def __init__(
        self,
        meta: dict[str, Any],
        catalog: tuple[CheckDef, ...] = CATALOG,
        suite: str = "id-jag-issuer",
    ):
        self.meta = meta
        self.catalog = catalog
        self.catalog_ids = tuple(c.id for c in catalog)
        # Matrix name of the check: `test-mcp-conformance (<suite>)`
        self.suite = suite
        self.results: dict[str, CheckResult] = {}
        self.unexpected: list[str] = []

    def add(self, result: CheckResult) -> CheckResult:
        if result.id not in self.catalog_ids or result.id in self.results:
            self.unexpected.append(result.id)
        self.results[result.id] = result
        return result

    def passed(self, check_id: str) -> bool:
        return check_id in self.results and self.results[check_id].status == PASS

    def verdict(self) -> tuple[bool, list[str]]:
        problems = []
        for check_id in self.catalog_ids:
            res = self.results.get(check_id)
            if res is None:
                problems.append(f"{check_id}: MISSING (check never executed)")
            elif res.status != PASS:
                problems.append(f"{check_id}: {res.status} - {res.summary}")
        problems.extend(f"{u}: UNEXPECTED/DUPLICATE check id" for u in self.unexpected)
        if not self.results:
            problems.append("zero checks executed")
        return not problems, problems

    def as_dict(self) -> dict:
        ok, problems = self.verdict()
        defs = {c.id: c for c in self.catalog}
        return {
            "suite": f"mcp-conformance-{self.suite}",
            "check_name": f"test-mcp-conformance ({self.suite})",
            "spec": DRAFT,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "meta": self.meta,
            "verdict": "PASS" if ok else "FAIL",
            "problems": problems,
            "expected_checks": list(self.catalog_ids),
            "checks": [
                {
                    **asdict(r),
                    "title": defs[r.id].title if r.id in defs else None,
                    "refs": list(defs[r.id].refs) if r.id in defs else [],
                    "upstream": defs[r.id].upstream if r.id in defs else None,
                }
                for r in self.results.values()
            ],
        }

    def write(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        data = self.as_dict()
        (directory / "report.json").write_text(json.dumps(data, indent=2, default=str))
        (directory / "report.md").write_text(render_markdown(data))
        (directory / "checks.junit.xml").write_text(render_junit(data))


def render_markdown(data: dict) -> str:
    lines = [
        f"## {data['check_name']}: {data['verdict']}",
        "",
        f"Spec: `{data['spec']}`",
        "",
        "| Check | Status | Summary |",
        "| --- | --- | --- |",
    ]
    by_id = {c["id"]: c for c in data["checks"]}
    for check_id in data["expected_checks"]:
        c = by_id.get(check_id)
        status = c["status"] if c else "MISSING"
        summary = (c["summary"] if c else "never executed").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check_id}` | {status} | {summary} |")
    if data["problems"]:
        lines += ["", "### Problems", ""] + [f"- {p}" for p in data["problems"]]
    return "\n".join(lines) + "\n"


def render_junit(data: dict) -> str:
    by_id = {c["id"]: c for c in data["checks"]}
    classname = quoteattr(data["suite"].removeprefix("mcp-conformance-").replace("-", "_"))
    classname = classname.replace('"', '"mcp.', 1)
    cases = []
    failures = 0
    for check_id in data["expected_checks"]:
        c = by_id.get(check_id)
        name = quoteattr(check_id)
        if c and c["status"] == PASS:
            cases.append(f"<testcase classname={classname} name={name}/>")
            continue
        failures += 1
        msg = c["summary"] if c else "check never executed"
        body = escape(json.dumps(c["details"] if c else {}, indent=2, default=str))
        status = c["status"] if c else "MISSING"
        cases.append(
            f"<testcase classname={classname} name={name}>"
            f"<failure message={quoteattr(f'{status}: {msg}')}>{body}</failure></testcase>"
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"<testsuite name={quoteattr(data['suite'])} tests=\"{len(cases)}\" "
        f'failures="{failures}">\n' + "\n".join(cases) + "\n</testsuite>\n"
    )
