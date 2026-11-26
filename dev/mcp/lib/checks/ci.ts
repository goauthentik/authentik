/**
 * @file Read lint jobs and generated paths from the Makefile and CI workflows.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ROOT } from "#dev/lib/git";
import { missing, notInstalled } from "#dev/lib/optional";

interface Workflow {
    jobs?: Record<
        string,
        {
            strategy?: { matrix?: { include?: unknown[]; job?: unknown[] } };
            steps?: { run?: string }[];
        }
    >;
}

async function workflow(root: string, name: string): Promise<Workflow> {
    const yaml = await import("yaml").catch(missing);

    if (!yaml) throw new Error(notInstalled("yaml"));

    return yaml.parse(readFileSync(join(root, ".github", "workflows", name), "utf8")) as Workflow;
}

/** Every `ci-lint-<job>` target in the Makefile. */
export function makefileLintTargets(root = ROOT): Set<string> {
    const text = readFileSync(join(root, "Makefile"), "utf8");

    return new Set([...text.matchAll(/^ci-lint-([a-z0-9-]+):/gm)].map((m) => m[1]!));
}

/** The `job:` entries of the lint matrix in ci-main.yml. */
export async function lintMatrix(root = ROOT): Promise<Set<string>> {
    const matrix = (await workflow(root, "ci-main.yml")).jobs?.lint?.strategy?.matrix ?? {};
    const entries = [...(matrix.include ?? []), ...(matrix.job ?? [])];

    return new Set(
        entries.map((e) =>
            e && typeof e === "object" ? String((e as { job: unknown }).job) : String(e),
        ),
    );
}

/** The paths the `test-gen` job diffs after regenerating. */
export async function genDiffPaths(root = ROOT): Promise<string[]> {
    for (const step of (await workflow(root, "ci-main.yml")).jobs?.["test-gen"]?.steps ?? []) {
        const match = /git diff --exit-code -- (.+)/.exec(step.run ?? "");

        if (match) return match[1]!.trim().split(/\s+/);
    }

    return [];
}
