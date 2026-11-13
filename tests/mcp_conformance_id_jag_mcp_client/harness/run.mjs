// Independent MCP client for the ID-JAG end-to-end harness: the official MCP TypeScript SDK
// (@modelcontextprotocol/client) driving MCP Enterprise-Managed Authorization against
// authentik in both roles, plus openid-client for the initial OpenID Connect sign-in.
//
// Reads a JSON config on stdin (see acceptance_mcp_client.py), runs every step, and writes a
// JSON document of per-check observations to `results_file`. Tokens, secrets and the
// password never leave this process: every string written is scrubbed first.
//
// The Python side (acceptance_mcp_client.py) owns the check catalog, gating and the report.

import { writeFileSync } from "node:fs";

import {
    Client,
    CrossAppAccessProvider,
    discoverAndRequestJwtAuthGrant,
    discoverOAuthServerInfo,
    exchangeJwtAuthGrant,
    extractWWWAuthenticateParams,
    requestJwtAuthorizationGrant,
    StreamableHTTPClientTransport,
} from "@modelcontextprotocol/client";
import { createRemoteJWKSet, decodeJwt, decodeProtectedHeader, jwtVerify } from "jose";
import * as oidc from "openid-client";

import { startMcpServer } from "./mcp_server.mjs";

const GRANT_TOKEN_EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange";
const GRANT_JWT_BEARER = "urn:ietf:params:oauth:grant-type:jwt-bearer";
const TT_ID_JAG = "urn:ietf:params:oauth:token-type:id-jag";
const TT_ID_TOKEN = "urn:ietf:params:oauth:token-type:id_token";
const GRANT_PROFILE_ID_JAG = "urn:ietf:params:oauth:grant-profile:id-jag";
const ID_JAG_TYP = "oauth-id-jag+jwt";
const SECRET_PARAMS = new Set(["assertion", "subject_token", "client_secret", "password", "code", "code_verifier"]);
const SECRET_FIELDS = new Set(["access_token", "id_token", "refresh_token"]);

// --------------------------------------------------------------------------- redaction
const secrets = new Set();
function addSecret(value) {
    if (typeof value === "string" && value.length >= 6) secrets.add(value);
}
const JWT_RE = /eyJ[\w-]+\.[\w-]+\.[\w-]*/g;
function scrub(text) {
    let out = String(text);
    // Longest first, so a secret containing another is replaced whole
    for (const secret of [...secrets].sort((a, b) => b.length - a.length)) {
        out = out.split(secret).join("<redacted>");
    }
    return out.replace(JWT_RE, "<redacted-jwt>");
}
const warnings = [];
for (const level of ["warn", "error", "log", "info"]) {
    console[level] = (...args) => warnings.push(scrub(`${level}: ${args.map(String).join(" ")}`));
}

// --------------------------------------------------------------------------- recording fetch
const exchanges = [];
function headerValue(headers, name) {
    if (!headers) return null;
    if (headers instanceof Headers) return headers.get(name);
    const key = Object.keys(headers).find((k) => k.toLowerCase() === name);
    return key ? headers[key] : null;
}
function classify(url, params) {
    const grant = params?.get("grant_type");
    if (grant === GRANT_TOKEN_EXCHANGE) return "token-exchange";
    if (grant === GRANT_JWT_BEARER) return "jwt-bearer";
    if (grant) return `token:${grant}`;
    if (url.pathname.includes("/.well-known/oauth-protected-resource")) return "prm";
    if (url.pathname.includes("/.well-known/")) return "as-metadata";
    if (url.pathname.startsWith("/mcp")) return "mcp";
    return "other";
}
/** fetch that records a redacted transcript of every request the SDK sends */
async function recFetch(input, init = {}) {
    const url = new URL(input instanceof Request ? input.url : String(input));
    const body = init.body;
    let params = null;
    if (typeof body === "string" || body instanceof URLSearchParams) {
        params = new URLSearchParams(typeof body === "string" ? body : body.toString());
        if (params.get("grant_type") === null && typeof body === "string" && body.startsWith("{")) params = null;
    }
    const authorization = headerValue(init.headers, "authorization");
    const entry = {
        kind: classify(url, params),
        method: (init.method ?? "GET").toUpperCase(),
        url: `${url.origin}${url.pathname}`,
    };
    if (params && entry.kind !== "mcp") {
        for (const [name, value] of params) {
            if (SECRET_PARAMS.has(name)) addSecret(value);
        }
        entry.params = Object.fromEntries(
            [...params].map(([name, value]) => [name, SECRET_PARAMS.has(name) ? "<redacted>" : value]),
        );
        entry.client_auth = authorization?.startsWith("Basic ")
            ? "client_secret_basic"
            : params.has("client_secret")
              ? "client_secret_post"
              : params.has("client_id")
                ? "none"
                : "unauthenticated";
    } else if (entry.kind === "mcp" && typeof body === "string") {
        try {
            entry.rpc = JSON.parse(body).method ?? null;
        } catch {
            entry.rpc = null;
        }
        entry.bearer = authorization?.startsWith("Bearer ") ?? false;
    }
    const response = await fetch(input, init);
    entry.status = response.status;
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("json") && entry.kind !== "mcp") {
        try {
            const json = await response.clone().json();
            entry.body = redactJson(json);
        } catch {
            entry.body = null;
        }
    }
    if (response.status === 401) entry.www_authenticate = response.headers.get("www-authenticate");
    exchanges.push(entry);
    return response;
}
function redactJson(value) {
    if (Array.isArray(value)) return value.map(redactJson);
    if (value && typeof value === "object") {
        return Object.fromEntries(
            Object.entries(value).map(([key, inner]) => {
                if (SECRET_FIELDS.has(key) && typeof inner === "string") {
                    addSecret(inner);
                    return [key, `<redacted len=${inner.length}>`];
                }
                return [key, redactJson(inner)];
            }),
        );
    }
    return value;
}
function mark() {
    return exchanges.length;
}
function since(start, kind) {
    return exchanges.slice(start).filter((entry) => !kind || entry.kind === kind);
}

// --------------------------------------------------------------------------- checks
class CheckFailed extends Error {
    constructor(summary, details = {}) {
        super(summary);
        this.details = details;
    }
}
function require(condition, summary, details = {}) {
    if (!condition) throw new CheckFailed(summary, details);
}
const results = {};
async function check(id, fn) {
    const start = mark();
    try {
        const out = (await fn()) ?? {};
        results[id] = { status: "PASS", summary: out.summary ?? "ok", details: out.details ?? {}, notes: out.notes ?? [] };
    } catch (error) {
        const failed = error instanceof CheckFailed;
        results[id] = {
            status: failed ? "FAIL" : "ERROR",
            summary: failed ? error.message : `${error?.name ?? "Error"}: ${error?.message ?? error}`,
            details: failed ? error.details : { stack: String(error?.stack ?? "").split("\n").slice(0, 8) },
            notes: [],
        };
    }
    results[id].http = since(start);
}
function errorOf(entry) {
    return entry?.body && typeof entry.body === "object" ? (entry.body.error ?? null) : null;
}
function describe(entry) {
    if (!entry) return "no request sent";
    const description = entry.body?.error_description ? ` (${entry.body.error_description})` : "";
    return `HTTP ${entry.status} ${errorOf(entry) ?? ""}${description}`.trim();
}
function sameIssuer(a, b) {
    return a === b || a.replace(/\/$/, "") === b.replace(/\/$/, "");
}

// --------------------------------------------------------------------------- main
const config = JSON.parse(await new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
}));
for (const client of [config.idp, config.idp_unlinked, config.ras]) addSecret(client.client_secret);
addSecret(config.login.password);

const state = {};

async function startServer() {
    // The MCP server knows its authorization server from configuration, like any deployment
    const response = await fetch(new URL(".well-known/openid-configuration", config.ras.issuer));
    const asMetadata = await response.json();
    return startMcpServer({ port: config.mcp_port, asMetadata });
}

/** A browser-like user agent: authentik login through the flow executor API, then the
 * authorization request, following nothing so the code lands in `Location`. */
function userAgent() {
    const jar = new Map();
    const send = async (url, init) => {
        const headers = new Headers(init.headers);
        if (jar.size) headers.set("cookie", [...jar].map(([k, v]) => `${k}=${v}`).join("; "));
        const response = await fetch(url, { ...init, headers, redirect: "manual" });
        for (const cookie of response.headers.getSetCookie()) {
            const [pair] = cookie.split(";");
            const index = pair.indexOf("=");
            jar.set(pair.slice(0, index).trim(), pair.slice(index + 1));
        }
        return response;
    };
    // Follows same-origin redirects (keeping cookies) unless `follow` is false
    return async (url, init = {}, follow = true) => {
        let current = new URL(url);
        let response = await send(current, init);
        for (let hops = 0; follow && hops < 5 && [301, 302, 303, 307, 308].includes(response.status); hops++) {
            const next = new URL(response.headers.get("location"), current);
            if (next.origin !== current.origin) break;
            const keep = [307, 308].includes(response.status);
            current = next;
            response = await send(current, keep ? init : { headers: init.headers });
        }
        return response;
    };
}

async function jsonOf(response, what) {
    const text = await response.text();
    try {
        return JSON.parse(text);
    } catch {
        throw new CheckFailed(`${what}: HTTP ${response.status}, not JSON`, {
            status: response.status,
            content_type: response.headers.get("content-type"),
            body: scrub(text.slice(0, 300)),
        });
    }
}

async function signIn(client) {
    const configuration = await oidc.discovery(new URL(client.issuer), client.client_id, client.client_secret, undefined, {
        execute: [oidc.allowInsecureRequests],
    });
    // Verify the ID token signature too (OIDC Core §3.1.3.7 allows relying on TLS instead)
    oidc.enableNonRepudiationChecks(configuration);
    const ua = userAgent();
    const executor = new URL(`/api/v3/flows/executor/${config.login.flow_slug}/?query=`, config.authentik);
    let response = await ua(executor, { headers: { accept: "application/json" } });
    let body = await jsonOf(response, "login flow");
    require(body.component === "ak-stage-identification", "login flow did not present identification", {
        component: body.component ?? null,
    });
    response = await ua(executor, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({
            component: "ak-stage-identification",
            uid_field: config.login.username,
            password: config.login.password,
        }),
    });
    body = await jsonOf(response, "login");
    require(body.component === "xak-flow-redirect", "login did not complete", { component: body.component ?? null });

    const codeVerifier = oidc.randomPKCECodeVerifier();
    const nonce = oidc.randomNonce();
    const stateParam = oidc.randomState();
    const authorizationUrl = oidc.buildAuthorizationUrl(configuration, {
        redirect_uri: client.redirect_uri,
        scope: "openid profile email",
        code_challenge: await oidc.calculatePKCECodeChallenge(codeVerifier),
        code_challenge_method: "S256",
        nonce,
        state: stateParam,
    });
    response = await ua(authorizationUrl, {}, false);
    const location = response.headers.get("location") ?? "";
    require(response.status === 302 && location.startsWith(client.redirect_uri), "authorize did not redirect to the client", {
        status: response.status,
        location: location.split("?")[0],
    });
    const tokens = await oidc.authorizationCodeGrant(configuration, new URL(location), {
        pkceCodeVerifier: codeVerifier,
        expectedNonce: nonce,
        expectedState: stateParam,
        idTokenExpected: true,
    });
    addSecret(tokens.id_token);
    addSecret(tokens.access_token);
    return { configuration, idToken: tokens.id_token, claims: tokens.claims() };
}

async function verifyIdJag(jag) {
    addSecret(jag);
    const jwks = createRemoteJWKSet(new URL(state.idpMetadata.jwks_uri));
    const { payload, protectedHeader } = await jwtVerify(jag, jwks, { issuer: state.idpMetadata.issuer });
    return { header: protectedHeader, claims: payload };
}

/** RFC 8693 request for an ID-JAG without `resource`, the parameter being OPTIONAL
 * (draft-06 §4.3). The SDK's helpers always send `resource`, so this is the harness's own
 * request, in the SDK's shape (client_secret_post). */
async function requestIdJagWithoutResource(ctx) {
    const params = new URLSearchParams({
        grant_type: GRANT_TOKEN_EXCHANGE,
        requested_token_type: TT_ID_JAG,
        audience: ctx.authorizationServerUrl,
        subject_token: state.sso.idToken,
        subject_token_type: TT_ID_TOKEN,
        client_id: config.idp.client_id,
        client_secret: config.idp.client_secret,
    });
    const response = await ctx.fetchFn(state.idpMetadata.token_endpoint, {
        method: "POST",
        headers: { "content-type": "application/x-www-form-urlencoded" },
        body: params.toString(),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(`token exchange failed: ${body.error}`);
    addSecret(body.access_token);
    return body.access_token;
}

function crossAppProvider(assertion) {
    return new CrossAppAccessProvider({
        assertion: async (ctx) => {
            state.assertionContexts.push({
                authorizationServerUrl: ctx.authorizationServerUrl,
                resourceUrl: ctx.resourceUrl,
                scope: ctx.scope ?? null,
            });
            const jag = await assertion(ctx);
            state.lastJag = jag;
            return jag;
        },
        clientId: config.ras.client_id,
        clientSecret: config.ras.client_secret,
        clientName: "authentik ID-JAG harness",
        expectedIssuer: state.rasIssuer,
        fetchFn: recFetch,
    });
}

/** Client.connect + tools/call whoami through StreamableHTTPClientTransport */
async function callWhoami(url, provider) {
    const transport = new StreamableHTTPClientTransport(new URL(url), { authProvider: provider, fetch: recFetch });
    const client = new Client({ name: "authentik-id-jag-harness", version: "1.0.0" });
    try {
        await client.connect(transport);
        const result = await client.callTool({ name: "whoami", arguments: {} });
        const text = result.content?.find((item) => item.type === "text")?.text ?? "{}";
        return JSON.parse(text);
    } finally {
        await client.close().catch(() => {});
    }
}

function tokenEndpointOutcome(entries) {
    return entries.map((entry) => ({
        kind: entry.kind,
        status: entry.status,
        error: errorOf(entry),
        client_auth: entry.client_auth,
        resource: entry.params?.resource ?? null,
        scope: entry.params?.scope ?? null,
    }));
}

async function expectTokenError(start, kind, errors, call) {
    let thrown = null;
    try {
        await call();
    } catch (error) {
        thrown = error;
    }
    const entry = since(start, kind).at(-1);
    require(entry, `no ${kind} request was sent`, { sdk_error: thrown ? scrub(thrown.message) : null });
    require(!entry.body?.access_token, `authentik ISSUED a token for an invalid ${kind} request`, { response: entry });
    require(
        entry.status === 400 && errors.includes(errorOf(entry)),
        `expected HTTP 400 error in [${errors.join(", ")}], got ${describe(entry)}`,
        { response: entry },
    );
    require(thrown !== null, "the SDK reported success for a refused request");
    return { entry, sdkError: scrub(thrown.message) };
}

const mcp = await startServer();
state.assertionContexts = [];
try {
    // ----------------------------------------------------------------- MCP discovery
    await check("mcp.discovery", async () => {
        const probe = await recFetch(mcp.urls.strict, {
            method: "POST",
            headers: { "content-type": "application/json", accept: "application/json, text/event-stream" },
            body: JSON.stringify({ jsonrpc: "2.0", id: 0, method: "ping" }),
        });
        const { resourceMetadataUrl } = extractWWWAuthenticateParams(probe);
        require(probe.status === 401 && resourceMetadataUrl, "MCP server did not challenge with resource_metadata", {
            status: probe.status,
        });
        const info = await discoverOAuthServerInfo(mcp.urls.strict, { resourceMetadataUrl, fetchFn: recFetch });
        const metadata = info.authorizationServerMetadata ?? {};
        require(info.resourceMetadata?.resource === mcp.urls.strict, "PRM resource is not the MCP server URL", {
            prm: info.resourceMetadata,
        });
        require(sameIssuer(String(info.authorizationServerUrl), config.ras.issuer), "PRM names another authorization server", {
            authorization_server: String(info.authorizationServerUrl),
        });
        require(metadata.issuer === config.ras.issuer, "authorization server metadata issuer mismatch", {
            issuer: metadata.issuer,
        });
        require((metadata.grant_types_supported ?? []).includes(GRANT_JWT_BEARER), "metadata lacks jwt-bearer", {
            grant_types_supported: metadata.grant_types_supported,
        });
        // The SDK's metadata schema drops members it doesn't know, so read the document
        // authentik served for the grant profile (the SDK itself never consults it)
        const served = exchanges.filter((e) => e.kind === "as-metadata" && e.status === 200).at(-1)?.body ?? {};
        require(
            (served.authorization_grant_profiles_supported ?? []).includes(GRANT_PROFILE_ID_JAG),
            "metadata lacks the ID-JAG grant profile",
            { authorization_grant_profiles_supported: served.authorization_grant_profiles_supported ?? null },
        );
        state.rasIssuer = metadata.issuer;
        state.rasMetadata = metadata;
        state.resource = info.resourceMetadata.resource;
        const tried = exchanges.filter((e) => e.kind === "as-metadata");
        const found = tried.find((e) => e.status === 200);
        const missed = tried.filter((e) => e.status !== 200).map((e) => `${new URL(e.url).pathname} (HTTP ${e.status})`);
        const notes = missed.length
            ? [
                  `the SDK first tried ${missed.join(", ")}: it drops the issuer's trailing slash when inserting ` +
                      "the well-known path (RFC 8414 §3.1 keeps the path component as is), then fell back to " +
                      "the OpenID Connect suffix form",
              ]
            : [];
        return {
            summary: `401 -> PRM -> authentik metadata via ${new URL(found.url).pathname}`,
            details: {
                prm: info.resourceMetadata,
                metadata_lookups: tried.map((e) => ({ url: e.url, status: e.status })),
                token_endpoint_auth_methods_supported: metadata.token_endpoint_auth_methods_supported,
            },
            notes,
        };
    });

    // ----------------------------------------------------------------- step 1: sign-in
    await check("sso.id-token", async () => {
        state.sso = await signIn(config.idp);
        state.idpMetadata = state.sso.configuration.serverMetadata();
        const { claims } = state.sso;
        require(claims.iss === config.idp.issuer, "ID token iss mismatch", { iss: claims.iss });
        return {
            summary: "openid-client: code + PKCE, ID token signature, iss, aud, nonce verified",
            details: { id_token_claims: { iss: claims.iss, aud: claims.aud, sub: claims.sub } },
        };
    });

    // ----------------------------------------------------------------- step 2: token exchange
    await check("exchange.id-jag", async () => {
        const start = mark();
        const result = await discoverAndRequestJwtAuthGrant({
            idpUrl: config.idp.issuer,
            audience: state.rasIssuer,
            resource: state.resource,
            idToken: state.sso.idToken,
            clientId: config.idp.client_id,
            clientSecret: config.idp.client_secret,
            fetchFn: recFetch,
        });
        const request = since(start, "token-exchange").at(-1);
        const { header, claims } = await verifyIdJag(result.jwtAuthGrant);
        state.resourceBoundJag = result.jwtAuthGrant;
        const problems = [];
        if (String(header.typ).toLowerCase().replace(/^application\//, "") !== ID_JAG_TYP) problems.push(`typ=${header.typ}`);
        if (claims.aud !== state.rasIssuer) problems.push(`aud ${JSON.stringify(claims.aud)} is not the Resource AS issuer`);
        if (claims.client_id !== config.ras.client_id) problems.push("client_id is not the client's id at the Resource AS");
        if (claims.sub !== state.sso.claims.sub) problems.push("sub is not the ID token subject");
        if (claims.resource !== state.resource) problems.push(`resource ${JSON.stringify(claims.resource)} is not the MCP server`);
        require(!problems.length, problems.join("; "), { header, claims });
        return {
            summary: `ID-JAG issued (SDK client auth: ${request.client_auth}; resource sent and embedded)`,
            details: {
                request: { client_auth: request.client_auth, params: request.params },
                header: { alg: header.alg, typ: header.typ },
                claims: { ...claims, jti: "<present>" },
            },
            notes: [
                "requestJwtAuthorizationGrant always sends `resource` (RFC 9728 resource of the MCP server) " +
                    "and authenticates with client_secret_post",
            ],
        };
    });

    await check("exchange.scope-forwarding", async () => {
        const start = mark();
        let result = null;
        let thrown = null;
        try {
            result = await requestJwtAuthorizationGrant({
                tokenEndpoint: state.idpMetadata.token_endpoint,
                audience: state.rasIssuer,
                resource: state.resource,
                idToken: state.sso.idToken,
                clientId: config.idp.client_id,
                clientSecret: config.idp.client_secret,
                scope: "mcp:tools",
                fetchFn: recFetch,
            });
        } catch (error) {
            thrown = error;
        }
        const entry = since(start, "token-exchange").at(-1);
        if (thrown) {
            require(
                entry?.status === 400 && errorOf(entry) === "invalid_scope",
                `scope request failed with ${describe(entry)}, not an explicit invalid_scope`,
                { response: entry },
            );
            return {
                summary: "scope refused with invalid_scope (explicit, never silently dropped)",
                notes: [
                    "CrossAppAccessProvider passes the MCP scope (from WWW-Authenticate or PRM scopes_supported) " +
                        "to the assertion callback and the SDK's examples forward it; authentik refuses any scope on " +
                        "ID-JAG requests, so such a flow fails at the token exchange",
                ],
            };
        }
        const { claims } = await verifyIdJag(result.jwtAuthGrant);
        const granted = new Set(String(result.scope ?? claims.scope ?? "").split(" ").filter(Boolean));
        require(
            String(claims.scope ?? "") === [...granted].join(" "),
            "scope silently changed between the response and the ID-JAG",
            { claims, response: entry },
        );
        return { summary: `granted ${[...granted].join(" ") || "nothing"} consistently` };
    });

    // ----------------------------------------------------------------- step 3: jwt-bearer
    await check("redeem.resource-bound", async () => {
        const start = mark();
        try {
            await exchangeJwtAuthGrant({
                tokenEndpoint: state.rasMetadata.token_endpoint,
                jwtAuthGrant: state.resourceBoundJag,
                clientId: config.ras.client_id,
                clientSecret: config.ras.client_secret,
                fetchFn: recFetch,
            });
        } catch (error) {
            const entry = since(start, "jwt-bearer").at(-1);
            // Differential: the same redemption with an ID-JAG that differs only in having no
            // `resource` claim (authentik doesn't return the refusal's cause)
            const control = mark();
            const jag = await requestIdJagWithoutResource({ authorizationServerUrl: state.rasIssuer, fetchFn: recFetch });
            await exchangeJwtAuthGrant({
                tokenEndpoint: state.rasMetadata.token_endpoint,
                jwtAuthGrant: jag,
                clientId: config.ras.client_id,
                clientSecret: config.ras.client_secret,
                fetchFn: recFetch,
            }).catch(() => {});
            const without = since(control, "jwt-bearer").at(-1);
            throw new CheckFailed(
                `authentik refused the SDK's resource-bound ID-JAG: ${describe(entry)}; the same ID-JAG ` +
                    `without the resource claim: ${describe(without)}. Providers can't declare governed ` +
                    "resources yet (RFC 8707 support)",
                {
                    resource: state.resource,
                    response: entry,
                    without_resource_claim: without,
                    sdk_error: scrub(error.message),
                },
            );
        }
        return { summary: "resource-bound ID-JAG redeemed" };
    });

    // Positive control for steps 3 and 4: the SDK's CrossAppAccessProvider + Client, with an
    // assertion callback that requests an ID-JAG without `resource`.
    let control = null;
    {
        const start = mark();
        const assertionStart = state.assertionContexts.length;
        let identity = null;
        let error = null;
        try {
            identity = await callWhoami(mcp.urls.issuerBound, crossAppProvider(requestIdJagWithoutResource));
        } catch (thrown) {
            error = thrown;
        }
        control = {
            identity,
            error,
            jag: state.lastJag,
            http: since(start),
            contexts: state.assertionContexts.slice(assertionStart),
            serverEvents: mcp.events.filter((event) => event.endpoint === "/mcp-issuer-bound"),
        };
    }

    await check("redeem.id-jag", async () => {
        const bearer = control.http.filter((entry) => entry.kind === "jwt-bearer");
        const ok = bearer.find((entry) => entry.status === 200);
        require(ok, `the SDK's jwt-bearer request failed: ${describe(bearer.at(-1))}`, {
            token_requests: tokenEndpointOutcome(control.http.filter((e) => e.params)),
            sdk_error: control.error ? scrub(control.error.message) : null,
        });
        require(String(ok.body?.token_type).toLowerCase() === "bearer", "token_type is not Bearer", { response: ok });
        const notes = [];
        if (ok.params.resource) {
            notes.push(
                `the SDK sent resource=${ok.params.resource} with the jwt-bearer grant (RFC 8707); authentik ` +
                    "ignored it, so the access token isn't audience-restricted (see mcp.audience-bound)",
            );
        }
        if (!("scope" in (ok.body ?? {}))) notes.push("granted scope not reported (draft-06 §4.4.1)");
        return {
            summary: `CrossAppAccessProvider redeemed the ID-JAG (client auth: ${ok.client_auth})`,
            details: {
                assertion_context: control.contexts[0],
                request: { client_auth: ok.client_auth, params: ok.params },
                response: ok.body,
            },
            notes,
        };
    });

    await check("mcp.tool-call", async () => {
        require(control.identity, `MCP call failed: ${scrub(control.error?.message ?? "no result")}`, {
            server_events: control.serverEvents,
        });
        require(sameIssuer(String(control.identity.iss), state.rasIssuer), "token issuer isn't the Resource AS", {
            identity: control.identity,
        });
        require(control.identity.client_id === config.ras.client_id, "token isn't issued to the MCP client", {
            identity: control.identity,
        });
        return {
            summary: "initialize + tools/call whoami as the signed-in user",
            details: { identity: control.identity, server_events: control.serverEvents },
        };
    });

    await check("mcp.audience-bound", async () => {
        const start = mark();
        const eventsStart = mcp.events.length;
        let identity = null;
        let error = null;
        try {
            identity = await callWhoami(mcp.urls.strict, crossAppProvider(requestIdJagWithoutResource));
        } catch (thrown) {
            error = thrown;
        }
        const events = mcp.events.slice(eventsStart).filter((event) => event.endpoint === "/mcp");
        const verified = events.filter((event) => event.outcome === "verified");
        if (!identity) {
            const last = verified.at(-1);
            throw new CheckFailed(
                last
                    ? `the MCP server refused authentik's access token: aud ${JSON.stringify(last.aud)} (the ` +
                          "client's client_id) doesn't name " +
                          "this resource (MCP token audience binding, RFC 8707 §2); authentik ignores the " +
                          "jwt-bearer `resource` parameter until RFC 8707 support lands"
                    : `the MCP flow failed before a token reached the server: ${scrub(error?.message ?? "")}`,
                {
                    resource: mcp.urls.strict,
                    server_events: events,
                    token_requests: tokenEndpointOutcome(since(start).filter((e) => e.params)),
                    sdk_error: error ? scrub(error.message) : null,
                },
            );
        }
        return { summary: "access token audience-restricted to the MCP server", details: { identity } };
    });

    await check("e2e.sdk-default", async () => {
        const start = mark();
        const eventsStart = mcp.events.length;
        let identity = null;
        let error = null;
        try {
            identity = await callWhoami(
                mcp.urls.strict,
                crossAppProvider(async (ctx) => {
                    const result = await discoverAndRequestJwtAuthGrant({
                        idpUrl: config.idp.issuer,
                        audience: ctx.authorizationServerUrl,
                        resource: ctx.resourceUrl,
                        idToken: state.sso.idToken,
                        clientId: config.idp.client_id,
                        clientSecret: config.idp.client_secret,
                        scope: ctx.scope,
                        fetchFn: ctx.fetchFn,
                    });
                    return result.jwtAuthGrant;
                }),
            );
        } catch (thrown) {
            error = thrown;
        }
        const tokenRequests = tokenEndpointOutcome(since(start).filter((e) => e.params));
        if (!identity) {
            const failed = since(start).filter((e) => e.params && e.status !== 200);
            const first = failed[0];
            const exchangesSent = tokenRequests.filter((r) => r.kind === "token-exchange").length;
            throw new CheckFailed(
                first
                    ? `the SDK's default Cross-App Access flow failed at the ${first.kind} step: ${describe(first)}` +
                          (exchangesSent > 1 ? ` (the SDK retried with a fresh ID-JAG ${exchangesSent - 1}x)` : "")
                    : `the SDK's default flow failed at the MCP server: ${scrub(error?.message ?? "")}`,
                {
                    token_requests: tokenRequests,
                    server_events: mcp.events.slice(eventsStart),
                    sdk_error: error ? scrub(error.message) : null,
                },
            );
        }
        return { summary: "SDK default flow reached the MCP server", details: { identity, token_requests: tokenRequests } };
    });

    await check("redeem.client-auth-methods", async () => {
        const outcomes = {};
        for (const authMethod of ["client_secret_basic", "client_secret_post"]) {
            const jag = await requestIdJagWithoutResource({ authorizationServerUrl: state.rasIssuer, fetchFn: recFetch });
            const start = mark();
            let error = null;
            try {
                await exchangeJwtAuthGrant({
                    tokenEndpoint: state.rasMetadata.token_endpoint,
                    jwtAuthGrant: jag,
                    clientId: config.ras.client_id,
                    clientSecret: config.ras.client_secret,
                    authMethod,
                    fetchFn: recFetch,
                });
            } catch (thrown) {
                error = thrown;
            }
            const entry = since(start, "jwt-bearer").at(-1);
            outcomes[authMethod] = { sent_as: entry?.client_auth, result: describe(entry), sdk_error: error ? scrub(error.message) : null };
        }
        const failed = Object.entries(outcomes).filter(([method, o]) => o.sent_as !== method || !o.result.startsWith("HTTP 200"));
        require(!failed.length, `authentik refused: ${failed.map(([m, o]) => `${m} -> ${o.result}`).join("; ")}`, { outcomes });
        return { summary: "exchangeJwtAuthGrant accepted with client_secret_basic and client_secret_post", details: { outcomes } };
    });

    // ----------------------------------------------------------------- negatives
    const exchangeWith = (overrides) => () =>
        requestJwtAuthorizationGrant({
            tokenEndpoint: state.idpMetadata.token_endpoint,
            audience: state.rasIssuer,
            resource: state.resource,
            idToken: state.sso.idToken,
            clientId: config.idp.client_id,
            clientSecret: config.idp.client_secret,
            fetchFn: recFetch,
            ...overrides,
        });

    await check("neg.exchange.wrong-audience", async () => {
        const { entry, sdkError } = await expectTokenError(
            mark(),
            "token-exchange",
            ["invalid_target"],
            exchangeWith({ audience: config.untrusted_audience }),
        );
        return { summary: `rejected: ${describe(entry)}`, details: { sdk_error: sdkError } };
    });

    await check("neg.exchange.unregistered-resource", async () => {
        const { entry, sdkError } = await expectTokenError(
            mark(),
            "token-exchange",
            ["invalid_target"],
            exchangeWith({ resource: new URL("/mcp-not-registered", mcp.base).href }),
        );
        return { summary: `rejected: ${describe(entry)}`, details: { sdk_error: sdkError } };
    });

    await check("neg.exchange.unlinked-app", async () => {
        const unlinked = await signIn(config.idp_unlinked);
        const { entry, sdkError } = await expectTokenError(
            mark(),
            "token-exchange",
            ["access_denied", "invalid_target"],
            exchangeWith({
                idToken: unlinked.idToken,
                clientId: config.idp_unlinked.client_id,
                clientSecret: config.idp_unlinked.client_secret,
            }),
        );
        const notes = [];
        if (errorOf(entry) !== "access_denied") {
            notes.push(
                `draft-06 §4.3.4.3 profiles access_denied for a client not authorized for the audience; authentik ` +
                    `returned ${errorOf(entry)} (allowed by RFC 8693 §2.2.2)`,
            );
        }
        return { summary: `rejected: ${describe(entry)}`, details: { sdk_error: sdkError }, notes };
    });

    await check("neg.redeem.replay", async () => {
        require(control.jag, "no redeemed ID-JAG to replay");
        const { entry, sdkError } = await expectTokenError(mark(), "jwt-bearer", ["invalid_grant"], () =>
            exchangeJwtAuthGrant({
                tokenEndpoint: state.rasMetadata.token_endpoint,
                jwtAuthGrant: control.jag,
                clientId: config.ras.client_id,
                clientSecret: config.ras.client_secret,
                fetchFn: recFetch,
            }),
        );
        return { summary: `rejected: ${describe(entry)}`, details: { sdk_error: sdkError } };
    });
} finally {
    await mcp.close();
}

const output = {
    sdk: {
        "@modelcontextprotocol/client": config.versions?.client ?? null,
        node: process.version,
    },
    mcp_urls: mcp.urls,
    // For cross-checks on the Python side; neither is a credential
    sso_sub: state.sso?.claims?.sub ?? null,
    results,
    sdk_warnings: warnings,
};
writeFileSync(config.results_file, scrub(JSON.stringify(output, null, 2)));
process.exit(0);
