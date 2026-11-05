# CIMD interoperability probe (prototype, do not merge)

Step 01b of the CIMD plan. Real MCP clients connect to a protected MCP server, which sends
them to an authentik provider that accepts URL-valued client IDs (Client ID Metadata
Documents). Everything the clients send is logged, and `run.sh summary` turns the logs into
the 01b findings checklist.

The code is deliberately unhardened: any metadata URL is admitted, fetches have no SSRF
protection, and codes and refresh tokens are not bound to the client. Run it only on
localhost. The launcher binds authentik's HTTP, HTTPS, and metrics listeners to both
`127.0.0.1` and `::1`, and its debug listeners to loopback. The MCP server binds both
loopback address families, never a wildcard address.

ID tokens returned by code redemption and refresh target the resolved URL client. Access
tokens retain the prototype's provider audience; the MCP verifier deliberately accepts
that audience as well as its resource URL. This is not resource-bound access-token
enforcement. Scoped discovery omits `registration_endpoint` until scoped registration is
supported; legacy discovery and DCR are unchanged.

## Pieces

| Piece | Where | Port |
|---|---|---|
| authentik with scoped CIMD endpoints for application `mcp-proto` | `authentik/providers/oauth2/prototype_cimd.py` | 9000 |
| Protected MCP server (tools `whoami`, `echo`) | `mcp_server.py` | 8765 |
| Logs | `/tmp/cimd-prototype/requests.jsonl` (authentik), `mcp.jsonl` (MCP server) | |

The provider uses its own database, `authentik_cimd`, created on first start. Access tokens
last 10 minutes so clients refresh during a session, and refresh tokens rotate on every use.
With 5-minute tokens, clients refreshed continuously, apparently because they refresh about
5 minutes before expiry. `run.sh mcp` reapplies the provider settings on every start.
Set `CIMD_PROTOTYPE_STATE` in every terminal to relocate both logs and run archives.
Rotating logs with `new-run` does not clear the metadata cache. A run without a metadata
fetch is therefore inconclusive; a URL client ID can reuse a warm cache. The live tail
follows the filename across rotation without needing a restart.

## Prerequisites

- Docker running with the `postgres` dev container on port 5432.
- `uv`, `jq`, and the Rust toolchain (the first `run.sh authentik` builds the server).
- On macOS, `lxml` and `xmlsec` built against the same `libxml2`, or SAML-related code may
  segfault. Not needed for this probe itself.

## Start (three terminals, from the repository root)

```bash
scripts/cimd-prototype/run.sh authentik   # 1: authentik server + worker
scripts/cimd-prototype/run.sh mcp         # 2: MCP server (creates the provider on first run)
scripts/cimd-prototype/run.sh tail        # 3: live view of the OAuth traffic
```

Before making requests, inspect the actual listeners (for example, with
`lsof -nP -iTCP -sTCP:LISTEN` on macOS). Ports 9000, 9443, 9300, and 8765 must show only
`127.0.0.1` or `[::1]`, not `*`, `0.0.0.0`, or `[::]`. Check debug ports too if enabled.
Both IPv4 and IPv6 loopback must be available; listener binding failures stop startup.

The browser login is `akadmin` with the password from `scripts/cimd-prototype/run.sh password`.

Check discovery before testing a client:

```bash
curl -si -X POST http://localhost:8765/mcp | grep -i www-authenticate
curl -s http://localhost:8765/.well-known/oauth-protected-resource/mcp
curl -s http://localhost:9000/.well-known/oauth-authorization-server/application/o/mcp-proto/ \
  | jq '{issuer, authorization_endpoint, token_endpoint, client_id_metadata_document_supported}'
```

## One run per client

```bash
scripts/cimd-prototype/run.sh new-run claude-code   # fresh logs for this client
# ... test the client (below) ...
scripts/cimd-prototype/run.sh save                  # writes runs/claude-code/summary.md
```

Each run covers four scenarios. Watch terminal 3 while doing them.

1. **First login.** Connect, log in, approve consent, call `whoami`. It should return
   `akadmin`. No `refresh_token` grant should follow straight away; if one does, note the
   interval between refreshes.
2. **Refresh.** Wait 6 minutes, call `whoami` again. Expect a `refresh_token` grant.
3. **Concurrent refresh.** Wait another 6 minutes. Open a second session or window of the
   same client, then call `whoami` in both at the same moment. Note whether both send the
   same refresh token (the summary marks it **REUSED**) and what the losing session does.
4. **Second process.** With a fresh session, check whether a new process reuses stored
   tokens or starts its own login.

### Claude Code

```bash
mkdir -p /tmp/cimd-client && cd /tmp/cimd-client
claude mcp add --transport http cimd-proto http://localhost:8765/mcp
claude
```

In Claude Code: `/mcp`, select `cimd-proto`, **Authenticate**. Then ask it to call the
`cimd-proto` `whoami` tool. For the concurrent refresh, run a second `claude` in the same
directory. Reset with `/mcp` > `cimd-proto` > **Clear authentication**, and remove the
server afterwards with `claude mcp remove cimd-proto`.

### VS Code

Open an empty folder with `.vscode/mcp.json`:

```json
{ "servers": { "cimd-proto": { "type": "http", "url": "http://localhost:8765/mcp" } } }
```

Click **Start** above the entry, or run **MCP: List Servers**. Accept the authentication
prompt and log in. Calling `#whoami` in Copilot Chat agent mode needs Copilot; without it,
starting the server and listing its tools still exercises discovery, login and tokens. For
the concurrent refresh, open a second window on the same folder. Reset with
**Authentication: Remove Dynamic Authentication Providers**.

### MCP Inspector (discovery debugging)

```bash
npx @modelcontextprotocol/inspector
```

Transport **Streamable HTTP**, URL `http://localhost:8765/mcp`, then **Auth Settings** >
**Guided OAuth Flow**. Its CIMD support needs an HTTPS metadata document listing its own
redirect URI, so expect it to fall back or stop; record where.

## What to hand in per client

`/tmp/cimd-prototype/runs/<client>/summary.md` answers most of the 01b checklist from the
logs: discovery order and 404s, the metadata document and its cache headers, redirect URI
forms and how they matched, `resource` and PKCE use, client authentication, DPoP, refresh
timing and reuse, and the token audience the MCP server saw. Fill in its "Manual notes"
section: client version, token sharing between processes, and what the user saw on errors.

## Simulated client (no browser)

`run.sh` does not include this, but the smoke test used in development is useful when
changing the probe itself: serve a metadata document with `python3 -m http.server` on a
loopback port (allowed by `AUTHENTIK_CIMD_PROTOTYPE__ALLOW_HTTP_LOCALHOST`), then call the
scoped authorize and token endpoints with that URL as `client_id`. See
`authentik/providers/oauth2/tests/test_prototype_cimd.py` for the request shapes.

## Regression checks

Use an explicitly isolated PostgreSQL test database, not the default `test_authentik`:

```bash
env AUTHENTIK_POSTGRESQL__NAME=cimd_review_core_20261105 \
  AUTHENTIK_POSTGRESQL__TEST__NAME=test_cimd_fix_poc_20261105 \
  PYTHONDONTWRITEBYTECODE=1 UV_NO_SYNC=1 \
  uv run --offline --with 'mcp==2.3.0' manage.py test --keepdb \
  authentik/providers/oauth2/tests/test_prototype_cimd.py \
  authentik/providers/oauth2/tests/test_prototype_harness.py
```

The MCP dependency is inline and optional, not a core dependency. Without `--with`, the
four MCP-specific harness tests skip; the summary, launcher, and live-tail tests still run.
The project mypy configuration tolerates absent optional MCP/Starlette imports and the
consequently untyped MCP tool decorators; check with the inline dependencies installed too.
Tests use temporary state and fixture credentials, never the demo's password or logs.

## Cleanup

```bash
docker exec postgres dropdb -U postgres authentik_cimd
rm -rf /tmp/cimd-prototype
```
