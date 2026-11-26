/**
 * @file The authentik-dev MCP server: stdio, no credentials, local dev database only.
 */

import { type Verdict, inspect } from "#dev-mcp/guard/verdict";
import { registerGenerated, registerJob, registerLint } from "#dev-mcp/server/checks";
import { INSTRUCTIONS } from "#dev-mcp/server/instructions";
import { registerSkills } from "#dev-mcp/server/skills";
import { registerStatus } from "#dev-mcp/server/status";

import { McpServer } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";

export async function build(verdict?: Verdict): Promise<McpServer> {
    const server = new McpServer(
        { name: "authentik-dev", version: "0.1.0" },
        { instructions: INSTRUCTIONS },
    );
    const startup = verdict ?? (await inspect()).verdict;

    registerStatus(server, startup);
    await registerSkills(server);
    registerJob(server);
    registerLint(server);
    if (startup.ok) registerGenerated(server);

    return server;
}

export async function serve(): Promise<void> {
    const server = await build();
    await server.connect(new StdioServerTransport());
}
