/**
 * @file Read the lint jobs and generated paths from the Makefile and CI workflows, so rules
 *   aren't copied by hand.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ROOT } from "./repo.ts";

import { parse as parseYAML } from "yaml";

interface Workflow {
    jobs?: Record<
        string,
        {
            strategy?: { matrix?: { include?: unknown[]; job?: unknown[] } };
            steps?: { run?: string }[];
        }
    >;
}

function workflow(root: string, name: string): Workflow {
    return parseYAML(readFileSync(join(root, ".github", "workflows", name), "utf8")) as Workflow;
}

/** Every `ci-lint-<job>` target in the Makefile. */
export function makefileLintTargets(root = ROOT): Set<string> {
    const text = readFileSync(join(root, "Makefile"), "utf8");
    return new Set([...text.matchAll(/^ci-lint-([a-z0-9-]+):/gm)].map((m) => m[1]!));
}

/** The `job:` entries of the lint matrix in ci-main.yml. */
export function lintMatrix(root = ROOT): Set<string> {
    const matrix = workflow(root, "ci-main.yml").jobs?.lint?.strategy?.matrix ?? {};
    const entries = [...(matrix.include ?? []), ...(matrix.job ?? [])];
    return new Set(
        entries.map((e) =>
            e && typeof e === "object" ? String((e as { job: unknown }).job) : String(e),
        ),
    );
}

/** The paths the `test-gen` job diffs after regenerating. */
export function genDiffPaths(root = ROOT): string[] {
    for (const step of workflow(root, "ci-main.yml").jobs?.["test-gen"]?.steps ?? []) {
        const match = /git diff --exit-code -- (.+)/.exec(step.run ?? "");
        if (match) return match[1]!.trim().split(/\s+/);
    }
    return [];
}
