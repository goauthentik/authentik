// The harness's MCP server fixture as a long-running process, for the e2e stack (stack/):
// reads the stack's config.json, discovers the Resource Authorization Server's metadata, and
// serves /mcp (audience-bound) and /mcp-issuer-bound on the given port, printing every
// authorization decision. Usage: node harness/serve.mjs CONFIG_JSON PORT

import { readFileSync } from "node:fs";

import { startMcpServer } from "./mcp_server.mjs";

const [configPath, port] = process.argv.slice(2);
const config = JSON.parse(readFileSync(configPath, "utf8"));
const response = await fetch(new URL(".well-known/openid-configuration", config.ras.issuer));
if (!response.ok) throw new Error(`Resource AS metadata: HTTP ${response.status}`);
const mcp = await startMcpServer({ port: Number(port), asMetadata: await response.json() });

process.stdout.write(`authorization server: ${config.ras.issuer}\n`);
process.stdout.write(`audience-bound:       ${mcp.urls.strict}\n`);
process.stdout.write(`issuer-bound:         ${mcp.urls.issuerBound}\n`);

// Events are recorded, then completed once verification finishes; print each when final
const printed = new WeakSet();
setInterval(() => {
    for (const event of mcp.events) {
        if (printed.has(event) || (event.outcome === "rejected" && !event.reason)) continue;
        printed.add(event);
        process.stdout.write(`${new Date().toISOString()} ${JSON.stringify(event)}\n`);
    }
}, 250);

for (const signal of ["SIGINT", "SIGTERM"]) {
    process.on(signal, async () => {
        await mcp.close();
        process.exit(0);
    });
}
