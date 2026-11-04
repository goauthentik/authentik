# ruff: noqa: PLR0912, PLR0915, PLR2004, E501
"""PROTOTYPE (01b), never merge: turn probe logs into the 01b findings checklist.

    python3 scripts/cimd-prototype/summarize.py /tmp/cimd-prototype[/runs/<name>]

Reads requests.jsonl (authentik side) and mcp.jsonl (MCP server side) and prints Markdown.
Items the logs cannot answer are listed at the end as manual notes.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def ts(row: dict) -> datetime:
    return datetime.fromisoformat(row["ts"])


def param(row: dict, key: str):
    return (row.get("query") or {}).get(key, (row.get("form") or {}).get(key))


def main(directory: Path):
    auth = load(directory / "requests.jsonl")
    mcp = load(directory / "mcp.jsonl")
    http = [r for r in auth if r.get("kind") == "http"]
    out = []
    p = out.append

    run = directory / "current-run"
    name = run.read_text().strip() if run.exists() else directory.name
    p(f"# CIMD probe summary: {name}\n")
    if not auth and not mcp:
        p("No log entries found.")
        print("\n".join(out))
        return
    every = sorted(auth + mcp, key=ts)
    p(f"- Window: {every[0]['ts']} to {every[-1]['ts']}")
    agents = Counter(
        r["headers"].get("User-Agent") for r in http if r.get("headers", {}).get("User-Agent")
    )
    agents.update(r.get("user_agent") for r in mcp if r.get("user_agent"))
    p("- User agents:")
    for agent, count in agents.most_common():
        p(f"  - `{agent}` ({count} requests)")
    client_ids = Counter(param(r, "client_id") for r in http if param(r, "client_id"))
    p("- client_id values sent:")
    for client_id, count in client_ids.most_common():
        kind = "URL (CIMD)" if str(client_id).startswith(("https://", "http://")) else "registered"
        p(f"  - `{client_id}`: {kind}, {count} requests")

    p("\n## Discovery\n")
    p("MCP server side, in order (first occurrence of each):\n")
    seen = set()
    for r in mcp:
        if r.get("kind") != "http":
            continue
        key = (r["method"], r["path"], r.get("code"))
        if key in seen:
            continue
        seen.add(key)
        extra = " (WWW-Authenticate sent)" if r.get("www_authenticate") else ""
        p(f"- `{r['method']} {r['path']}` -> {r.get('code')}{extra}")
    p("\nauthentik side, in order (first occurrence of each):\n")
    seen = set()
    for r in http:
        if ".well-known" not in r["path"] and not r["path"].endswith("/jwks/"):
            continue
        key = (r["method"], r["path"], r["status"])
        if key in seen:
            continue
        seen.add(key)
        p(f"- `{r['method']} {r['path']}` -> {r['status']}")

    p("\n## Client metadata documents\n")
    fetches = [r for r in auth if r.get("kind") == "metadata_fetch"]
    by_client = defaultdict(list)
    for r in fetches:
        by_client[r["client_id"]].append(r)
    if not by_client:
        p("No metadata fetches: the client did not use a URL client_id.")
    for client_id, rows in by_client.items():
        last = rows[-1]
        p(f"### `{client_id}`\n")
        p(f"- Fetched {len(rows)} time(s); last status {last.get('status', last.get('error'))}")
        p(f"- Response headers: `{json.dumps(last.get('headers', {}))}`")
        p("\n```json\n" + json.dumps(last.get("document"), indent=2) + "\n```\n")
    for r in auth:
        if r.get("kind") in ("metadata_invalid", "client_unresolved"):
            p(f"- {r['kind']}: `{r.get('client_id')}` ({r.get('reason')})")

    p("\n## Redirect URIs\n")
    redirects = Counter(
        (r["redirect_uri"], r.get("matched")) for r in auth if r.get("kind") == "redirect_uri"
    )
    for (uri, matched), count in redirects.items():
        p(f"- `{uri}`: {matched or 'NO MATCH'} ({count}x)")
    if not redirects:
        p("None recorded.")

    p("\n## Authorization requests\n")
    authorize = [r for r in http if r["path"].endswith("/authorize/")]
    p(f"- Count: {len(authorize)}")
    for key in (
        "response_type",
        "scope",
        "resource",
        "code_challenge_method",
        "prompt",
        "dpop_jkt",
        "response_mode",
    ):
        values = Counter(str(r["query"].get(key)) for r in authorize)
        p(f"- `{key}`: " + ", ".join(f"{v} ({c}x)" for v, c in values.items()))
    pkce = sum(1 for r in authorize if r["query"].get("code_challenge"))
    p(f"- `code_challenge` present: {pkce}/{len(authorize)}")

    p("\n## Token requests\n")
    token = [r for r in http if r["path"].endswith("/token/") and r["method"] == "POST"]
    for grant, rows in sorted(
        {
            g: [r for r in token if r["form"].get("grant_type") == g]
            for g in {r["form"].get("grant_type") for r in token}
        }.items(),
        key=lambda item: str(item[0]),
    ):
        statuses = Counter(r["status"] for r in rows)
        errors = Counter((r.get("response") or {}).get("error") for r in rows if r["status"] >= 400)
        p(f"### `{grant}` ({len(rows)} requests)\n")
        p(f"- Status: {dict(statuses)}" + (f"; errors {dict(errors)}" if errors else ""))
        p(f"- `resource` sent: {sum(1 for r in rows if r['form'].get('resource'))}/{len(rows)}")
        p(
            f"- `code_verifier` sent: {sum(1 for r in rows if r['form'].get('code_verifier'))}/{len(rows)}"
        )
        p(f"- `scope` sent: {Counter(str(r['form'].get('scope')) for r in rows)}")
        auth_modes = Counter(
            (
                "basic"
                if r["headers"].get("Authorization", "").startswith("Basic")
                else "client_secret_post" if r["form"].get("client_secret") else "none"
            )
            for r in rows
        )
        p(f"- Client authentication: {dict(auth_modes)}")
        p(f"- DPoP header: {sum(1 for r in rows if 'DPoP' in r['headers'])}/{len(rows)}")
        p(f"- Origin header (browser client): {Counter(r['headers'].get('Origin') for r in rows)}")

    p("\n## Refresh behaviour\n")
    issued = {}  # refresh token sha -> issue time
    for r in token:
        body = r.get("response") or {}
        if isinstance(body.get("refresh_token"), dict):
            issued[body["refresh_token"]["sha"]] = ts(r)
    refreshes = [r for r in token if r["form"].get("grant_type") == "refresh_token"]
    uses = Counter(
        r["form"]["refresh_token"]["sha"] for r in refreshes if r["form"].get("refresh_token")
    )
    for r in refreshes:
        sha = (r["form"].get("refresh_token") or {}).get("sha")
        age = ts(r) - issued[sha] if sha in issued else None
        error = (r.get("response") or {}).get("error")
        p(
            f"- {r['ts'][11:19]} refresh token `{sha}` "
            f"(age {age if age is not None else 'unknown'}) -> {r['status']}"
            + (f" {error}" if error else "")
            + (" **REUSED**" if uses.get(sha, 0) > 1 else "")
        )
    if not refreshes:
        p("No refresh requests. Keep the session open past the 5-minute access token lifetime.")
    reused = [sha for sha, count in uses.items() if count > 1]
    if reused:
        p(f"\nRefresh tokens used more than once (concurrency or retry): {reused}")

    p("\n## MCP server\n")
    accepted = [r for r in mcp if r.get("kind") == "token_accepted"]
    rejected = [r for r in mcp if r.get("kind") == "token_rejected"]
    p(f"- Tokens accepted: {len(accepted)}, rejected: {len(rejected)}")
    if accepted:
        p(f"- `aud` values: {Counter(str(r.get('aud')) for r in accepted)}")
        p(
            f"- Audience contained the MCP resource URL: {sum(1 for r in accepted if r.get('aud_is_resource'))}/{len(accepted)}"
        )
    for r in rejected[:5]:
        p(f"  - rejected: {r.get('error')}")
    versions = Counter(r.get("mcp_protocol_version") for r in mcp if r.get("kind") == "http")
    p(f"- MCP-Protocol-Version headers: {dict(versions)}")
    p(f"- DPoP on MCP requests: {sum(1 for r in mcp if r.get('dpop'))}")

    p("\n## Manual notes (not answerable from logs)\n")
    p("- Client name and exact version:")
    p("- Did a second process/window reuse the first one's tokens, or log in again?")
    p("- What did the user see on failure (error text, retry, silent re-login)?")
    p("- Anything unexpected in the consent screen or browser handoff:")
    print("\n".join(out))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cimd-prototype"))  # nosec
