/**
 * @file The authentik-dev MCP server: stdio, no credentials, local dev database only.
 */

import { checkGenerated } from "./checks/generated.ts";
import { lint } from "./checks/lint.ts";
import { LANGUAGE_SERVER_INSTALL, publicEnvironment } from "./discovery.ts";
import { inspect, suggestedAllowlist, type Verdict } from "./guard.ts";
import * as jobs from "./jobs.ts";
import { DEFAULT_BASE, ROOT, branch, mergeBase } from "./repo.ts";
import { SKILLS_DIR, listSkills, readSkill } from "./skills.ts";

import { McpServer, type ToolAnnotations } from "@modelcontextprotocol/server";
import { loadSkills } from "@modelcontextprotocol/server/ext/skills/node";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import * as z from "zod";

/** The first 512 characters carry the rules: Codex only guarantees that much. */
export const INSTRUCTIONS = `\
Use these tools to check authentik changes before you report them done. Call akdev_generated \
after changing models, serializers or API views. Call akdev_lint with no paths to lint the whole \
change. Use akdev_skill to read a repo skill before answering how-to questions. Results list what \
they skipped and couldn't tell; repeat that when you summarize. Nothing here applies changes or \
contacts GitHub.

Tool guide:
- akdev_status first: it shows how this machine runs Postgres and containers, and whether the \
database guard allowed the database tools. If a tool is missing, the guard said why.
- akdev_generated and akdev_lint can take minutes. They return a jobId; poll akdev_job.
- Commands in results are written for this machine's setup. Show them to the person rather than \
running ones that change the database.
- A result's \`unknown\` list means the tool couldn't tell. Don't report those items as passing.
`;

const READ_ONLY: ToolAnnotations = {
    readOnlyHint: true,
    destructiveHint: false,
    openWorldHint: false,
};
const WRITES_TREE: ToolAnnotations = {
    readOnlyHint: false,
    destructiveHint: false,
    openWorldHint: false,
};

function reply(data: object) {
    const structured = JSON.parse(JSON.stringify(data)) as Record<string, unknown>;
    return {
        content: [{ type: "text" as const, text: JSON.stringify(structured, null, 2) }],
        structuredContent: structured,
    };
}

export async function build(verdict?: Verdict): Promise<McpServer> {
    const server = new McpServer(
        { name: "authentik-dev", version: "0.1.0" },
        { instructions: INSTRUCTIONS },
    );
    const startup = verdict ?? (await inspect()).verdict;

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
            const { env, verdict: now } = await inspect();
            const notes = now.allowlistChanged
                ? ["The database allowlist changed since the last run. Check that change."]
                : [];
            if (env) {
                notes.push(
                    ...Object.entries(env.languageServers)
                        .filter(([, v]) => v === null)
                        .map(
                            ([name]) =>
                                `Optional: ${name} isn't on PATH, so editors and Claude Code's ` +
                                `LSP plugins can't use it. Install: ${LANGUAGE_SERVER_INSTALL[name]}`,
                        ),
                );
            }
            return reply({
                repo: ROOT,
                branch: branch(),
                base: DEFAULT_BASE,
                mergeBase: mergeBase(),
                environment: env && publicEnvironment(env),
                guard: now,
                allowlistSuggestion: env && suggestedAllowlist(env, now),
                databaseTools: startup.ok
                    ? "enabled"
                    : "disabled for this session; restart the server once the guard passes",
                notes,
            });
        },
    );

    server.registerTool(
        "akdev_skill",
        {
            description:
                "Read one of authentik's repo skills: how to set up the dev environment, run the " +
                "backend or frontend, run tests, fix lint, write docs, open a PR, or cut a " +
                "release. Use it before answering a how-to question about working on authentik.",
            inputSchema: z.object({
                name: z
                    .string()
                    .optional()
                    .describe("Skill to read, such as 'testing'. Omit to list them."),
            }),
            annotations: READ_ONLY,
        },
        async ({ name }) => {
            if (!name) return reply({ skills: listSkills() });
            const content = readSkill(name);
            return reply(
                content === null
                    ? { error: `no skill named ${JSON.stringify(name)}`, skills: listSkills() }
                    : { name, content },
            );
        },
    );

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

    server.registerTool(
        "akdev_lint",
        {
            description:
                "Run the CI lint jobs that cover an authentik change (ruff, black, mypy, bandit, " +
                "cspell, clippy, rustfmt, oxlint, tsc, docs checks) with the commands CI uses. " +
                "Use before saying a change is done, or when a CI lint job failed. Returns a " +
                "jobId to poll with akdev_job. Writes files only with fix=true; a missing CI " +
                "placeholder file may be created.",
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
        async ({ paths, base, fix }) =>
            reply(jobs.start("akdev_lint", "lint", () => lint(paths ?? [], base, fix))),
    );

    if (startup.ok) {
        server.registerTool(
            "akdev_generated",
            {
                description:
                    "Check whether authentik's generated files are stale after a code change: " +
                    "missing Django migrations, schema.yml, blueprints/schema.json, the API " +
                    "clients, and locales. The same checks as the test-gen and pending-migrations " +
                    "CI jobs. Use after changing a model, serializer, viewset or API view. " +
                    "Returns a jobId to poll with akdev_job.",
                inputSchema: z.object({
                    regenerate: z
                        .enum(["none", "schema"])
                        .default("none")
                        .describe("'schema' rewrites schema.yml and blueprints/schema.json."),
                    base: z.string().default(DEFAULT_BASE).describe("Branch to compare against."),
                }),
                annotations: WRITES_TREE,
            },
            async ({ regenerate, base }) =>
                reply(
                    jobs.start("akdev_generated", "generated", () =>
                        checkGenerated(regenerate, base),
                    ),
                ),
        );
    }

    try {
        (await loadSkills(SKILLS_DIR)).attach(server);
    } catch (error) {
        // akdev_skill still serves them.
        process.stderr.write(`skills extension not attached: ${(error as Error).message}\n`);
    }
    return server;
}

export async function serve(): Promise<void> {
    const server = await build();
    await server.connect(new StdioServerTransport());
}
