/**
 * @file Register long-running lint and generated-file checks.
 */

import { checkGenerated } from "#dev-mcp/checks/generated";
import { lint } from "#dev-mcp/checks/lint";
import * as jobs from "#dev-mcp/results/jobs";
import { JOB_NOTE, READ_ONLY, WRITES_TREE, reply, runJob } from "#dev-mcp/server/shared";
import { DEFAULT_BASE } from "#dev/lib/git";

import type { McpServer } from "@modelcontextprotocol/server";
import * as z from "zod";

export function registerJob(server: McpServer): void {
    server.registerTool(
        "akdev_job",
        {
            description:
                "The state and, once finished, the result of a long-running authentik check.",
            inputSchema: z.object({
                jobId: z.string().describe("The jobId a long-running tool returned."),
            }),
            annotations: READ_ONLY,
        },
        async ({ jobId }) =>
            reply(
                jobs.get(jobId) ?? {
                    error: `no job ${JSON.stringify(jobId)}; jobs are dropped when the server restarts`,
                },
            ),
    );
}

export function registerLint(server: McpServer): void {
    server.registerTool(
        "akdev_lint",
        {
            description:
                "Run the CI lint jobs that cover an authentik change (ruff, black, mypy, bandit, " +
                "cspell, clippy, rustfmt, oxlint, tsc, docs checks) with the commands CI uses. " +
                "Use before saying a change is done, or when a CI lint job failed. Writes files " +
                "only with fix=true; a missing CI placeholder file may be created. " +
                JOB_NOTE,
            inputSchema: z.object({
                paths: z
                    .array(z.string())
                    .optional()
                    .describe("Files to lint. Omit to lint everything changed since base."),
                base: z.string().default(DEFAULT_BASE).describe("Branch to compare against."),
                fix: z
                    .boolean()
                    .default(false)
                    .describe("Apply auto-fixes (black, ruff, rustfmt, oxlint, oxfmt)."),
            }),
            annotations: WRITES_TREE,
        },
        async ({ paths, base, fix }, ctx) =>
            runJob(ctx, "akdev_lint", "lint", (progress) => lint(paths ?? [], base, fix, progress)),
    );
}

/**
 * Only registered when the database guard passes: it runs Django against the database.
 */
export function registerGenerated(server: McpServer): void {
    server.registerTool(
        "akdev_generated",
        {
            description:
                "Check whether authentik's generated files are stale after a code change: " +
                "missing Django migrations, schema.yml, blueprints/schema.json, the API " +
                "clients, and locales. The same checks as the test-gen and pending-migrations " +
                "CI jobs. Use after changing a model, serializer, viewset or API view. " +
                JOB_NOTE,
            inputSchema: z.object({
                regenerate: z
                    .enum(["none", "schema"])
                    .default("none")
                    .describe("'schema' rewrites schema.yml and blueprints/schema.json."),
                base: z.string().default(DEFAULT_BASE).describe("Branch to compare against."),
            }),
            annotations: WRITES_TREE,
        },
        async ({ regenerate, base }, ctx) =>
            runJob(ctx, "akdev_generated", "generated", (progress) =>
                checkGenerated(regenerate, base, progress),
            ),
    );
}
