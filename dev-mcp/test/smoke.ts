#!/usr/bin/env node
/**
 * @file Protocol smoke test: start the server over stdio, list the tools, call them.
 *   A script rather than a vitest test, because it needs the real dev environment (Postgres and
 *   the guard's verdict). Run with `node dev-mcp/test/smoke.ts`.
 */

import { ROOT } from "#dev-mcp/core/repo";

import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";

const client = new Client({ name: "dev-mcp-smoke", version: "0.0.0" });
await client.connect(
    new StdioClientTransport({
        command: process.execPath,
        args: ["dev-mcp/main.ts", "serve"],
        cwd: ROOT,
        env: process.env as Record<string, string>,
    }),
);

type Payload = Record<string, any>;

async function call(name: string, args: Record<string, unknown> = {}): Promise<Payload> {
    const result = await client.callTool({ name, arguments: args });
    return (result.structuredContent ?? {}) as Payload;
}

const instructions = client.getInstructions() ?? "";
console.log(
    `server: ${client.getServerVersion()?.name}; instructions: ${instructions.length} chars`,
);

const { tools } = await client.listTools();
for (const tool of tools)
    console.log(`  tool ${tool.name} readOnly=${tool.annotations?.readOnlyHint}`);

const status = await call("akdev_status");
console.log(`guard ok: ${status.guard.ok}; postgres: ${status.environment.postgres.kind}`);

const skill = await call("akdev_skill", { name: "testing" });
console.log(`skill 'testing': ${String(skill.content ?? "").length} chars`);
console.log(
    `traversal refused: ${"error" in (await call("akdev_skill", { name: "../../AGENTS" }))}`,
);

if (tools.some((t) => t.name === "akdev_generated")) {
    let job = await call("akdev_generated");
    while (job.state === "running") {
        await new Promise((r) => setTimeout(r, 1000));
        job = await call("akdev_job", { jobId: job.jobId });
    }
    console.log(`akdev_generated: ${job.state}: ${job.result?.summary ?? job.error}`);
}

await client.close();
