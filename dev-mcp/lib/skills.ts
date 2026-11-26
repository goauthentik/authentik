/**
 * @file The repo's Agent Skills from `.agents/skills/`, for clients that didn't load them.
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { missing } from "#dev-mcp/optional";
import { ROOT } from "#dev-mcp/repo";

export const SKILLS_DIR = join(ROOT, ".agents", "skills");

export interface SkillSummary {
    name: string;
    description: string;
}

/** Skill names, from their directories. Needs nothing installed. */
export function skillNames(): string[] {
    return readdirSync(SKILLS_DIR)
        .filter((name) => {
            try {
                return statSync(join(SKILLS_DIR, name, "SKILL.md")).isFile();
            } catch {
                return false;
            }
        })
        .sort();
}

export async function listSkills(): Promise<SkillSummary[]> {
    const yaml = await import("yaml").catch(missing);
    return skillNames().map((name) => {
        const text = readFileSync(join(SKILLS_DIR, name, "SKILL.md"), "utf8");
        const front = /^---\n([\s\S]*?)\n---/.exec(text)?.[1];
        const meta: unknown = front && yaml ? yaml.parse(front) : {};
        const description =
            meta && typeof meta === "object" ? (meta as { description?: unknown }).description : "";
        return {
            name,
            description: String(description ?? "")
                .replace(/\s+/g, " ")
                .trim(),
        };
    });
}

/** A skill's SKILL.md by name. Only names of skill directories; no path traversal. */
export function readSkill(name: string): string | null {
    if (!/^[a-z0-9-]+$/.test(name) || !skillNames().includes(name)) return null;
    return readFileSync(join(SKILLS_DIR, name, "SKILL.md"), "utf8");
}
