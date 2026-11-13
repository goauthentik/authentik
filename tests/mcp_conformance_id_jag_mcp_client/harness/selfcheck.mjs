// Self-check of the harness's MCP server fixture, independent of authentik: a local stub
// authorization server (its own key and JWKS) signs access tokens, and the official SDK
// client calls the fixture with them. Confirms that a red mcp.* check is authentik's
// behavior, not the fixture's: the audience-bound endpoint accepts a token whose aud is the
// resource and refuses one whose aud is a client ID, and both refuse ID-JAGs.

import assert from "node:assert/strict";
import { createServer } from "node:http";

import { Client, StreamableHTTPClientTransport } from "@modelcontextprotocol/client";
import { exportJWK, generateKeyPair, SignJWT } from "jose";

import { startMcpServer } from "./mcp_server.mjs";

async function listen(handler) {
    const server = createServer(handler);
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    return { server, port: server.address().port };
}

const { privateKey, publicKey } = await generateKeyPair("RS256");
const jwk = { ...(await exportJWK(publicKey)), kid: "selfcheck", alg: "RS256", use: "sig" };
const as = await listen((req, res) => {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ keys: [jwk] }));
});
const issuer = `http://localhost:${as.port}/as/`;
const asMetadata = {
    issuer,
    authorization_endpoint: `${issuer}authorize`,
    token_endpoint: `${issuer}token`,
    jwks_uri: `http://localhost:${as.port}/jwks`,
    response_types_supported: ["code"],
};
const probe = await listen(() => {});
const port = probe.port;
await new Promise((resolve) => probe.server.close(resolve));
const mcp = await startMcpServer({ port, asMetadata });

function sign(claims, typ = "at+jwt") {
    return new SignJWT({ scope: "", client_id: "selfcheck-client", ...claims })
        .setProtectedHeader({ alg: "RS256", kid: "selfcheck", typ })
        .setIssuer(issuer)
        .setSubject("selfcheck-user")
        .setIssuedAt()
        .setExpirationTime("5m")
        .sign(privateKey);
}

async function whoami(url, token) {
    const transport = new StreamableHTTPClientTransport(new URL(url), {
        authProvider: { token: async () => token },
    });
    const client = new Client({ name: "selfcheck", version: "1.0.0" });
    try {
        await client.connect(transport);
        const result = await client.callTool({ name: "whoami", arguments: {} });
        return JSON.parse(result.content[0].text);
    } finally {
        await client.close().catch(() => {});
    }
}

/** True when the call failed because the fixture's verifier rejected the token */
async function refused(url, token) {
    const start = mcp.events.length;
    try {
        await whoami(url, token);
    } catch {
        // The bearer gate answered with a challenge, rather than the call failing elsewhere
        return mcp.events.slice(start).some((event) => event.outcome === "challenged");
    }
    return false;
}

const checks = [];
async function check(name, fn) {
    await fn();
    checks.push(name);
}

try {
    await check("401 challenge names the protected resource metadata", async () => {
        const response = await fetch(mcp.urls.strict, { method: "POST" });
        assert.equal(response.status, 401);
        const challenge = response.headers.get("www-authenticate") ?? "";
        const url = /resource_metadata="([^"]+)"/.exec(challenge)?.[1];
        assert.ok(url, challenge);
        const prm = await (await fetch(url)).json();
        assert.equal(prm.resource, mcp.urls.strict);
        assert.deepEqual(prm.authorization_servers, [issuer]);
    });
    await check("audience-bound endpoint accepts a token for its resource", async () => {
        const identity = await whoami(mcp.urls.strict, await sign({ aud: mcp.urls.strict }));
        assert.equal(identity.sub, "selfcheck-user");
    });
    await check("audience-bound endpoint refuses a token whose aud is a client ID", async () => {
        assert.ok(await refused(mcp.urls.strict, await sign({ aud: "selfcheck-client" })));
    });
    await check("issuer-bound endpoint accepts a token whose aud is a client ID", async () => {
        const identity = await whoami(mcp.urls.issuerBound, await sign({ aud: "selfcheck-client" }));
        assert.equal(identity.iss, issuer);
    });
    await check("both endpoints refuse an ID-JAG", async () => {
        const jag = await sign({ aud: mcp.urls.strict }, "oauth-id-jag+jwt");
        assert.ok(await refused(mcp.urls.strict, jag));
        assert.ok(await refused(mcp.urls.issuerBound, jag));
    });
    await check("both endpoints refuse a token from another issuer's key", async () => {
        const other = await generateKeyPair("RS256");
        const forged = await new SignJWT({ aud: mcp.urls.strict })
            .setProtectedHeader({ alg: "RS256", kid: "selfcheck" })
            .setIssuer(issuer)
            .setSubject("attacker")
            .setExpirationTime("5m")
            .sign(other.privateKey);
        assert.ok(await refused(mcp.urls.strict, forged));
        assert.ok(await refused(mcp.urls.issuerBound, forged));
    });
} finally {
    await mcp.close();
    as.server.close();
}
for (const name of checks) process.stdout.write(`ok - ${name}\n`);
process.stdout.write(`selfcheck passed (${checks.length} checks)\n`);
