// Browser-driven ID-JAG walkthrough for the e2e stack (stack/browser.sh): a small web app that
// plays the MCP client's part. You sign in to authentik (the IdP) in your browser, and the app
// then runs the rest of MCP Enterprise-Managed Authorization with the official MCP SDK against
// the stack's long-running MCP server, showing each step:
//
//   1. OpenID Connect sign-in (code + PKCE) at the IdP provider    -> ID token
//   2. RFC 8693 token exchange at the IdP provider                  -> ID-JAG
//   3. RFC 7523 jwt-bearer at the Resource AS provider (SDK)        -> access token
//   4. MCP initialize + tools/call whoami (SDK Client)              -> the MCP server's view
//
// Then it runs the SDK's unmodified flow against the audience-bound endpoint, which fails
// until authentik's Resource AS supports RFC 8707 (see README "Expected red").
//
// Tokens never reach the page: it shows decoded headers and claims only.
// Usage: node harness/browser.mjs CONFIG_JSON PORT MCP_PORT

import { readFileSync } from "node:fs";
import { createServer } from "node:http";

import {
    Client,
    CrossAppAccessProvider,
    discoverAndRequestJwtAuthGrant,
    StreamableHTTPClientTransport,
} from "@modelcontextprotocol/client";
import { decodeJwt, decodeProtectedHeader } from "jose";
import * as oidc from "openid-client";

const GRANT_TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange";
const TT_ID_JAG = "urn:ietf:params:oauth:token-type:id-jag";
const TT_ID_TOKEN = "urn:ietf:params:oauth:token-type:id_token";
const SHOWN_PARAMS = ["grant_type", "requested_token_type", "subject_token_type", "audience", "resource", "scope", "client_id"];

const [configPath, port, mcpPort] = process.argv.slice(2);
const config = JSON.parse(readFileSync(configPath, "utf8"));
const base = `http://localhost:${port}`;
const redirectUri = `${base}/callback`;
const mcp = {
    strict: `http://localhost:${mcpPort}/mcp`,
    issuerBound: `http://localhost:${mcpPort}/mcp-issuer-bound`,
};

const idp = await oidc.discovery(new URL(config.idp.issuer), config.idp.client_id, config.idp.client_secret, undefined, {
    execute: [oidc.allowInsecureRequests],
});
oidc.enableNonRepudiationChecks(idp);
const idpMetadata = idp.serverMetadata();

// ------------------------------------------------------------------------------ helpers
function jwtView(token) {
    try {
        return { header: decodeProtectedHeader(token), claims: decodeJwt(token) };
    } catch {
        return null;
    }
}

/** A fetch that records token endpoint calls: parameters, client auth, status, and the
 * decoded (never raw) token it returned */
function tracingFetch(log) {
    return async (input, init = {}) => {
        const url = String(input instanceof Request ? input.url : input);
        const response = await fetch(input, init);
        const body = init.body instanceof URLSearchParams ? init.body : typeof init.body === "string" ? new URLSearchParams(init.body) : null;
        if (!body?.get("grant_type")) return response;
        const headers = new Headers(init.headers);
        const entry = {
            url: new URL(url).pathname,
            params: Object.fromEntries(SHOWN_PARAMS.filter((name) => body.has(name)).map((name) => [name, body.get(name)])),
            client_auth: headers.get("authorization")?.startsWith("Basic ")
                ? "client_secret_basic"
                : body.has("client_secret")
                  ? "client_secret_post"
                  : "none",
            status: response.status,
        };
        const json = await response.clone().json().catch(() => ({}));
        if (json.error) entry.error = json.error;
        if (json.access_token) {
            entry.issued_token_type = json.issued_token_type ?? json.token_type;
            entry.token = jwtView(json.access_token);
        }
        log.push(entry);
        return response;
    };
}

async function exchangeWithoutResource(idToken, audience, fetchFn) {
    // `resource` is OPTIONAL (draft-06 §4.3); the SDK's helpers always send it
    const params = new URLSearchParams({
        grant_type: GRANT_TOKEN_EXCHANGE,
        requested_token_type: TT_ID_JAG,
        audience,
        subject_token: idToken,
        subject_token_type: TT_ID_TOKEN,
        client_id: config.idp.client_id,
        client_secret: config.idp.client_secret,
    });
    const response = await fetchFn(idpMetadata.token_endpoint, {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: params,
    });
    const json = await response.json();
    if (!response.ok) throw new Error(`token exchange failed: ${json.error}`);
    return json.access_token;
}

async function whoami(url, assertion, fetchFn) {
    const authProvider = new CrossAppAccessProvider({
        assertion,
        clientId: config.ras.client_id,
        clientSecret: config.ras.client_secret,
        clientName: "authentik ID-JAG browser demo",
        expectedIssuer: config.ras.issuer,
        fetchFn,
    });
    const transport = new StreamableHTTPClientTransport(new URL(url), { authProvider, fetch: fetchFn });
    const client = new Client({ name: "authentik-id-jag-browser-demo", version: "1.0.0" });
    try {
        await client.connect(transport);
        const result = await client.callTool({ name: "whoami", arguments: {} });
        return JSON.parse(result.content?.find((item) => item.type === "text")?.text ?? "{}");
    } finally {
        await client.close().catch(() => {});
    }
}

async function walkthrough(idToken) {
    const runs = [];
    // The flow that works today: ID-JAG without `resource`, issuer-bound MCP endpoint
    {
        const log = [];
        const fetchFn = tracingFetch(log);
        const run = { title: "Steps 2 to 4: ID-JAG without resource, issuer-bound MCP endpoint", url: mcp.issuerBound, log };
        try {
            run.identity = await whoami(mcp.issuerBound, (ctx) => exchangeWithoutResource(idToken, ctx.authorizationServerUrl, fetchFn), fetchFn);
        } catch (error) {
            run.error = error.message;
        }
        runs.push(run);
    }
    // The SDK's documented flow, unmodified: resource-bound ID-JAG, audience-bound endpoint
    {
        const log = [];
        const fetchFn = tracingFetch(log);
        const run = { title: "The SDK's default flow: resource-bound ID-JAG, audience-bound MCP endpoint", url: mcp.strict, log, expectedRed: true };
        try {
            run.identity = await whoami(
                mcp.strict,
                async (ctx) =>
                    (
                        await discoverAndRequestJwtAuthGrant({
                            idpUrl: config.idp.issuer,
                            audience: ctx.authorizationServerUrl,
                            resource: String(ctx.resourceUrl),
                            idToken,
                            clientId: config.idp.client_id,
                            clientSecret: config.idp.client_secret,
                            fetchFn,
                        })
                    ).jwtAuthGrant,
                fetchFn,
            );
        } catch (error) {
            run.error = error.message;
        }
        runs.push(run);
    }
    return runs;
}

// ------------------------------------------------------------------------------ pages
const esc = (value) =>
    String(value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const json = (value) => `<pre>${esc(JSON.stringify(value, null, 2))}</pre>`;

function page(body) {
    return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ID-JAG walkthrough</title><style>
:root{color-scheme:light dark;--bg:#fff;--fg:#1b1b1f;--muted:#5f6368;--line:#d9d9de;--ok:#1a7f37;--bad:#c62828;--warn:#9a6700;--code:#f5f5f7}
@media (prefers-color-scheme:dark){:root{--bg:#141417;--fg:#ececf1;--muted:#a0a0aa;--line:#33333a;--ok:#4cc26a;--bad:#ff6b6b;--warn:#e3b341;--code:#1e1e23}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:960px;padding:24px 16px}
h1{font-size:22px}h2{font-size:18px;margin-top:32px;border-top:1px solid var(--line);padding-top:16px}
.muted{color:var(--muted)}.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}
pre{background:var(--code);padding:12px;border-radius:6px;overflow-x:auto;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid var(--line);padding:6px;text-align:left;vertical-align:top}
a.button{display:inline-block;padding:10px 16px;border-radius:6px;background:#fd4b2d;color:#fff;text-decoration:none;font-weight:600}
details{margin:8px 0}code{background:var(--code);padding:1px 4px;border-radius:4px}
</style></head><body>${body}</body></html>`;
}

function home() {
    return page(`<h1>ID-JAG walkthrough</h1>
<p>This page plays the MCP client. Sign in at authentik (the IdP); the client then exchanges your ID token for an ID-JAG,
redeems it at authentik's Resource Authorization Server with the official MCP SDK, and calls the MCP server as you.</p>
<p><a class="button" href="/login">Sign in with authentik</a></p>
<p class="muted">Demo user: <code>${esc(config.login.username)}</code>. Its password, and the admin login:
<code>jq '.login, .admin' tests/mcp_conformance_id_jag_mcp_client/.stack/config.json</code></p>
<table>
<tr><th>IdP (token exchange)</th><td><code>${esc(config.idp.issuer)}</code></td></tr>
<tr><th>Resource AS (jwt-bearer)</th><td><code>${esc(config.ras.issuer)}</code></td></tr>
<tr><th>MCP server</th><td><code>${esc(mcp.strict)}</code> (audience-bound), <code>${esc(mcp.issuerBound)}</code> (issuer-bound)</td></tr>
<tr><th>authentik admin</th><td><a href="${esc(config.authentik)}/if/admin/#/core/providers">providers</a>,
<a href="${esc(config.authentik)}/if/admin/#/core/sources">sources</a>,
<a href="${esc(config.authentik)}/if/admin/#/events/log">event log</a></td></tr>
</table>`);
}

function logTable(log) {
    if (!log.length) return "<p class='muted'>No token endpoint requests.</p>";
    const rows = log
        .map(
            (entry) => `<tr><td>${esc(entry.url)}</td><td>${esc(entry.params.grant_type?.split(":").pop() ?? "")}</td>
<td>${esc(entry.client_auth)}</td><td>${entry.params.resource ? `<code>${esc(entry.params.resource)}</code>` : "—"}</td>
<td class="${entry.status === 200 ? "ok" : "bad"}">${entry.status}${entry.error ? ` ${esc(entry.error)}` : ""}</td></tr>`,
        )
        .join("");
    const tokens = log
        .filter((entry) => entry.token)
        .map((entry) => `<details><summary>${esc(entry.params.grant_type?.split(":").pop())}: issued <code>${esc(entry.issued_token_type ?? "")}</code></summary>${json(entry.token)}</details>`)
        .join("");
    return `<table><tr><th>Endpoint</th><th>Grant</th><th>Client auth</th><th>resource</th><th>Result</th></tr>${rows}</table>${tokens}`;
}

function result(idTokenView, runs) {
    const sections = runs
        .map((run) => {
            const status = run.identity
                ? `<p class="ok"><strong>The MCP server accepted the call.</strong></p>${json(run.identity)}`
                : `<p class="${run.expectedRed ? "warn" : "bad"}"><strong>${run.expectedRed ? "Failed, as expected today" : "Failed"}:</strong> ${esc(run.error)}</p>`;
            const note = run.expectedRed
                ? `<p class="muted">authentik's Resource AS can't declare governed resources yet (RFC 8707), so it refuses an ID-JAG whose
<code>resource</code> claim names the MCP server, and issues access tokens whose <code>aud</code> is the client ID. The SDK retries once.</p>`
                : "";
            return `<h2>${esc(run.title)}</h2><p class="muted">MCP endpoint: <code>${esc(run.url)}</code></p>${status}${note}${logTable(run.log)}`;
        })
        .join("");
    return page(`<h1>ID-JAG walkthrough</h1><p><a href="/">Start over</a></p>
<h2>Step 1: signed in at the IdP</h2><p class="ok">ID token verified by openid-client (signature, iss, aud, nonce).</p>
<details><summary>ID token</summary>${json(idTokenView)}</details>${sections}
<p class="muted">The MCP server pane logs each authorization decision; authentik's pane logs every token request.</p>`);
}

// ------------------------------------------------------------------------------ server
const pending = new Map();
const server = createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", base);
    const send = (status, html, headers = {}) => {
        res.writeHead(status, { "content-type": "text/html; charset=utf-8", ...headers });
        res.end(html);
    };
    try {
        if (url.pathname === "/") return send(200, home());
        if (url.pathname === "/login") {
            const verifier = oidc.randomPKCECodeVerifier();
            const nonce = oidc.randomNonce();
            const state = oidc.randomState();
            pending.set(state, { verifier, nonce });
            const target = oidc.buildAuthorizationUrl(idp, {
                redirect_uri: redirectUri,
                scope: "openid profile email",
                code_challenge: await oidc.calculatePKCECodeChallenge(verifier),
                code_challenge_method: "S256",
                nonce,
                state,
            });
            return send(302, "", { location: target.href });
        }
        if (url.pathname === "/callback") {
            const state = url.searchParams.get("state") ?? "";
            const flow = pending.get(state);
            pending.delete(state);
            if (!flow) return send(400, page("<p>Unknown or reused sign-in. <a href='/'>Start over</a></p>"));
            const tokens = await oidc.authorizationCodeGrant(idp, url, {
                pkceCodeVerifier: flow.verifier,
                expectedNonce: flow.nonce,
                expectedState: state,
                idTokenExpected: true,
            });
            const runs = await walkthrough(tokens.id_token);
            return send(200, result(jwtView(tokens.id_token), runs));
        }
        return send(404, page("<p>Not found. <a href='/'>Start over</a></p>"));
    } catch (error) {
        return send(500, page(`<p class="bad">${esc(error.message)}</p><p><a href="/">Start over</a></p>`));
    }
});
server.listen(Number(port), "127.0.0.1", () => {
    process.stdout.write(`ID-JAG walkthrough: ${base}/\n`);
});
