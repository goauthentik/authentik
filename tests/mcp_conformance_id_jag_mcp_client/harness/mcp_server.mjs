// Minimal MCP server (official TypeScript server SDK) acting as a Protected Resource for the
// ID-JAG harness. Its RFC 9728 Protected Resource Metadata names one authorization server:
// the authentik provider configured as the Resource Authorization Server.
//
// Two endpoints, with separate metadata (path-aware, RFC 9728 §3.1):
//   /mcp              spec-compliant: only accepts access tokens whose audience is this
//                     resource (MCP Authorization "Token Audience Binding", RFC 8707 §2),
//                     through the server SDK's `expectedResource`.
//   /mcp-issuer-bound accepts any valid access token from the authorization server named in
//                     its metadata (signature, iss, exp), without an audience comparison. It
//                     is the positive control for reaching an MCP server at all.
//
// Tokens are verified independently of authentik's code, with `jose` against the JWKS
// discovered from the authorization server's metadata.

import { createServer } from "node:http";

import {
    buildOAuthProtectedResourceMetadata,
    getOAuthProtectedResourceMetadataUrl,
    McpServer,
    OAuthError,
    OAuthErrorCode,
    requireBearerAuth,
    WebStandardStreamableHTTPServerTransport,
} from "@modelcontextprotocol/server";
import { createRemoteJWKSet, decodeProtectedHeader, jwtVerify } from "jose";

export const STRICT_PATH = "/mcp";
export const ISSUER_BOUND_PATH = "/mcp-issuer-bound";
const ID_JAG_TYP = "oauth-id-jag+jwt";

/** Aud values that are resource identifiers (absolute http(s) URLs). */
function resourceAudiences(aud) {
    const values = Array.isArray(aud) ? aud : aud === undefined ? [] : [aud];
    return values.filter((value) => {
        try {
            const url = new URL(value);
            return url.protocol === "https:" || url.protocol === "http:";
        } catch {
            return false;
        }
    });
}

function tokenVerifier(asMetadata, events, label, expectedResource) {
    const jwks = createRemoteJWKSet(new URL(asMetadata.jwks_uri));
    return {
        async verifyAccessToken(token) {
            const event = { endpoint: label, outcome: "rejected" };
            events.push(event);
            try {
                const header = decodeProtectedHeader(token);
                if (String(header.typ ?? "").toLowerCase().endsWith(ID_JAG_TYP)) {
                    throw new OAuthError(OAuthErrorCode.InvalidToken, "an ID-JAG is not an access token");
                }
                const { payload } = await jwtVerify(token, jwks, { issuer: asMetadata.issuer });
                const resources = resourceAudiences(payload.aud);
                // The SDK compares AuthInfo.resource with expectedResource; report the one
                // matching this server when the token names several.
                const resource =
                    resources.find((value) => expectedResource && sameResource(value, expectedResource)) ??
                    resources[0];
                Object.assign(event, {
                    outcome: "verified",
                    aud: payload.aud,
                    resource: resource ?? null,
                });
                return {
                    token,
                    clientId: String(payload.azp ?? payload.client_id ?? ""),
                    scopes: typeof payload.scope === "string" ? payload.scope.split(" ").filter(Boolean) : [],
                    expiresAt: payload.exp,
                    resource: resource ? new URL(resource) : undefined,
                    extra: { sub: payload.sub, iss: payload.iss, aud: payload.aud },
                };
            } catch (error) {
                event.reason = error instanceof Error ? error.message : String(error);
                if (error instanceof OAuthError) throw error;
                throw new OAuthError(OAuthErrorCode.InvalidToken, "access token failed verification");
            }
        },
    };
}

function sameResource(a, b) {
    const norm = (value) => {
        const url = new URL(value);
        url.hash = "";
        return url.href.replace(/\/$/, "");
    };
    return norm(a) === norm(b);
}

function buildMcpServer() {
    const server = new McpServer({ name: "authentik-id-jag-harness-resource", version: "1.0.0" });
    server.registerTool(
        "whoami",
        { description: "Report the identity of the access token this request was authorized with" },
        async (ctx) => {
            const auth = ctx.http?.authInfo;
            const identity = {
                sub: auth?.extra?.sub ?? null,
                iss: auth?.extra?.iss ?? null,
                aud: auth?.extra?.aud ?? null,
                client_id: auth?.clientId ?? null,
                scopes: auth?.scopes ?? [],
            };
            return { content: [{ type: "text", text: JSON.stringify(identity) }] };
        },
    );
    return server;
}

async function toWebRequest(req, base) {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const headers = new Headers();
    for (const [name, value] of Object.entries(req.headers)) {
        if (value !== undefined) headers.set(name, Array.isArray(value) ? value.join(", ") : value);
    }
    const hasBody = !["GET", "HEAD"].includes(req.method ?? "GET");
    return new Request(new URL(req.url ?? "/", base), {
        method: req.method,
        headers,
        body: hasBody ? Buffer.concat(chunks) : undefined,
    });
}

async function writeWebResponse(res, response) {
    res.writeHead(response.status, Object.fromEntries(response.headers));
    if (response.body) {
        for await (const chunk of response.body) res.write(chunk);
    }
    res.end();
}

/**
 * Start the MCP server on `port` (loopback). `asMetadata` is the RFC 8414 metadata of the
 * Resource Authorization Server. Returns { base, urls, events, close }.
 */
export async function startMcpServer({ port, asMetadata }) {
    const base = `http://localhost:${port}`;
    const events = [];
    const endpoints = new Map();
    for (const [path, strict] of [
        [STRICT_PATH, true],
        [ISSUER_BOUND_PATH, false],
    ]) {
        const resourceUrl = new URL(path, base);
        const prm = buildOAuthProtectedResourceMetadata({
            oauthMetadata: asMetadata,
            resourceServerUrl: resourceUrl,
            resourceName: `ID-JAG harness ${strict ? "(audience-bound)" : "(issuer-bound)"}`,
        });
        const prmUrl = getOAuthProtectedResourceMetadataUrl(resourceUrl);
        const gate = requireBearerAuth({
            verifier: tokenVerifier(asMetadata, events, path, strict ? resourceUrl.href : undefined),
            resourceMetadataUrl: prmUrl,
            ...(strict ? { expectedResource: resourceUrl } : {}),
        });
        endpoints.set(path, { gate, prm, prmPath: new URL(prmUrl).pathname });
    }

    const server = createServer(async (req, res) => {
        try {
            const request = await toWebRequest(req, base);
            const { pathname } = new URL(request.url);
            for (const [path, endpoint] of endpoints) {
                if (pathname === endpoint.prmPath) {
                    return writeWebResponse(res, Response.json(endpoint.prm));
                }
                if (pathname === path) {
                    const auth = await endpoint.gate(request);
                    if (auth instanceof Response) {
                        events.push({ endpoint: path, outcome: "challenged", status: auth.status });
                        return writeWebResponse(res, auth);
                    }
                    // Stateless: a server and transport per request
                    const mcp = buildMcpServer();
                    const transport = new WebStandardStreamableHTTPServerTransport({
                        sessionIdGenerator: undefined,
                        enableJsonResponse: true,
                    });
                    await mcp.connect(transport);
                    return writeWebResponse(res, await transport.handleRequest(request, { authInfo: auth }));
                }
            }
            return writeWebResponse(res, new Response("not found", { status: 404 }));
        } catch (error) {
            events.push({ outcome: "server_error", reason: String(error?.message ?? error) });
            if (!res.headersSent) res.writeHead(500);
            res.end();
        }
    });
    await new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(port, "127.0.0.1", resolve);
    });
    return {
        base,
        urls: {
            strict: new URL(STRICT_PATH, base).href,
            issuerBound: new URL(ISSUER_BOUND_PATH, base).href,
        },
        events,
        close: () => new Promise((resolve) => server.close(() => resolve())),
    };
}
