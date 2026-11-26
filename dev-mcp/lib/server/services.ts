/**
 * @file Register tools for managing the local development containers.
 */

import type { Runtime } from "#dev-mcp/environment/runtime";
import { COMPOSE_FILE, SERVICES, composeCommand, services } from "#dev-mcp/environment/services";
import type { Verdict } from "#dev-mcp/guard/verdict";
import { JOB_NOTE, reply, runJob } from "#dev-mcp/server/shared";

import type { McpServer } from "@modelcontextprotocol/server";
import * as z from "zod";

export function registerServices(server: McpServer, runtime: Runtime, startup: Verdict): void {
    if (!composeCommand(runtime, "status")) return;

    server.registerTool(
        "akdev_services",
        {
            description:
                `Bring authentik's dev containers (${COMPOSE_FILE}: ${SERVICES.join(", ")}) up ` +
                `or down with this machine's ${runtime.compose}. 'up' pulls images on first use ` +
                "and waits for Postgres; 'down' removes the containers but keeps their volumes, " +
                "so the data comes back with 'up'. 'status' lists them. Ask the person before " +
                "'up' or 'down'. For 'up' and 'down': " +
                JOB_NOTE,
            inputSchema: z.object({
                action: z.enum(["up", "down", "status"]).describe("What to do."),
            }),
            annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: true },
            // Claude Code asks the person every time, whatever their allow rules say.
            _meta: { "anthropic/requiresUserInteraction": true },
        },
        async ({ action }, ctx) => {
            if (action === "status") return reply(await services(runtime, "status"));

            return runJob(ctx, "akdev_services", "services", async (progress) => {
                const result = await services(runtime, action, progress);

                // The database tools are decided once, when the server starts.
                if (action === "up" && result.ok && !startup.ok) {
                    result.unsure(
                        "database tools",
                        "the guard refused the database at startup; restart the server " +
                            "(/mcp in Claude Code) once akdev_status shows it passing",
                    );

                    result.finish(result.headline);
                }

                return result;
            });
        },
    );
}
