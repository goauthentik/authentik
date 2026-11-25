/**
 * @file The repo's Agent Skills from `.agents/skills/`, for clients that didn't load them.
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { ROOT } from "./repo.ts";

import { parse as parseYAML } from "yaml";

export const SKILLS_DIR = join(ROOT, ".agents", "skills");

export interface SkillSummary {
    name: string;
    description: string;
}

function frontmatter(text: string): Record<string, unknown> {
    const match = /^---\n([\s\S]*?)\n---/.exec(text);
    if (!match) return {};
    const data = parseYAML(match[1]!);
    return data && typeof data === "object" ? (data as Record<string, unknown>) : {};
}

export function listSkills(): SkillSummary[] {
    return readdirSync(SKILLS_DIR)
        .filter((name) => {
            try {
                return statSync(join(SKILLS_DIR, name, "SKILL.md")).isFile();
            } catch {
                return false;
            }
        })
        .sort()
        .map((dir) => {
            const meta = frontmatter(readFileSync(join(SKILLS_DIR, dir, "SKILL.md"), "utf8"));
            return {
                name: String(meta.name ?? dir),
                description: String(meta.description ?? "")
                    .replace(/\s+/g, " ")
                    .trim(),
            };
        });
}

/** A skill's SKILL.md by name. Only names of skill directories; no path traversal. */
export function readSkill(name: string): string | null {
    if (!listSkills().some((s) => s.name === name) || !/^[a-z0-9-]+$/.test(name)) return null;
    return readFileSync(join(SKILLS_DIR, name, "SKILL.md"), "utf8");
}
