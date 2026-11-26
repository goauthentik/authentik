/**
 * @file The repo's skills, as `akdev_skill` and through the Skills-over-MCP extension.
 */

import { SKILLS_DIR, listSkills, readSkill } from "#dev-mcp/agent/skills";
import { READ_ONLY, reply } from "#dev-mcp/server/shared";

import type { McpServer } from "@modelcontextprotocol/server";
import { loadSkills } from "@modelcontextprotocol/server/ext/skills/node";
import * as z from "zod";

export async function registerSkills(server: McpServer): Promise<void> {
    // For clients without Skills-over-MCP, such as Codex.
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
            if (!name) return reply({ skills: await listSkills() });
            const content = readSkill(name);
            return reply(
                content === null
                    ? {
                          error: `no skill named ${JSON.stringify(name)}`,
                          skills: await listSkills(),
                      }
                    : { name, content },
            );
        },
    );

    try {
        (await loadSkills(SKILLS_DIR)).attach(server);
    } catch (error) {
        // akdev_skill still serves them.
        process.stderr.write(`skills extension not attached: ${(error as Error).message}\n`);
    }
}
