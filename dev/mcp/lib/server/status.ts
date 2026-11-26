/**
 * @file `akdev_status`: what the server sees, and the guard's verdict.
 */

import { LANGUAGE_SERVER_INSTALL, publicEnvironment } from "#dev-mcp/environment/discover";
import { type Verdict, inspect, suggestedAllowlist } from "#dev-mcp/guard/verdict";
import { READ_ONLY, reply } from "#dev-mcp/server/shared";
import { DEFAULT_BASE, ROOT, branch, mergeBase } from "#dev/lib/git";

import type { McpServer } from "@modelcontextprotocol/server";

export function registerStatus(server: McpServer, startup: Verdict): void {
    server.registerTool(
        "akdev_status",
        {
            description:
                "What the authentik dev server sees: the repo, branch and base, how this machine " +
                "runs Postgres and containers (Docker, Podman or native), the resolved config and " +
                "where each value came from, and the database guard's verdict. Call this first, " +
                "or when a tool is missing or a dev setup command fails.",
            annotations: READ_ONLY,
        },
        async () => {
            const { env, verdict } = await inspect();

            const notes = verdict.allowlistChanged
                ? ["The database allowlist changed since the last run. Check that change."]
                : [];

            for (const [name, found] of Object.entries(env?.languageServers ?? {})) {
                if (found !== null) continue;

                notes.push(
                    `Optional: ${name} isn't on PATH, so editors and Claude Code's LSP plugins ` +
                        `can't use it. Install: ${LANGUAGE_SERVER_INSTALL[name]}`,
                );
            }

            return reply({
                repo: ROOT,
                branch: branch(),
                base: DEFAULT_BASE,
                mergeBase: mergeBase(),
                environment: env && publicEnvironment(env),
                guard: verdict,
                allowlistSuggestion: env && suggestedAllowlist(env, verdict),
                databaseTools: startup.ok
                    ? "enabled"
                    : "disabled for this session; restart the server once the guard passes",
                notes,
            });
        },
    );
}
