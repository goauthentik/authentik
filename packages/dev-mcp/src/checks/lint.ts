/**
 * @file Run the CI lint jobs that cover a change, with the commands CI uses.
 */

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

import { lintMatrix, makefileLintTargets } from "../ci.ts";
import { DEFAULT_BASE, ROOT, changedFiles, fingerprint } from "../repo.ts";
import { Result } from "../result.ts";
import { run, tail, which } from "../run.ts";

const JOB_TIMEOUT = 30 * 60_000;
const PY_DIRS = ["authentik/", "packages/", "tests/", "scripts/", "lifecycle/"];

/**
 * CI's lint matrix writes these placeholders before every job. Only missing ones are created,
 * so a real web build is never overwritten.
 */
const CI_PLACEHOLDERS = ["web/dist/standalone/loading/startup.html"];

type Covers = (path: string) => boolean;

const basename = (p: string) => p.slice(p.lastIndexOf("/") + 1);
const isPython: Covers = (p) => p.endsWith(".py") && PY_DIRS.some((d) => p.startsWith(d));
const isCargoManifest: Covers = (p) =>
    ["Cargo.toml", "Cargo.lock"].includes(basename(p)) || p === ".cargo/deny.toml";
const isRust: Covers = (p) => p.endsWith(".rs") || isCargoManifest(p);
const isWeb: Covers = (p) => p.startsWith("web/") && !p.startsWith("web/xliff/");
const isNodeScript: Covers = (p) =>
    p.startsWith("scripts/node/") ||
    (!p.includes("/") && (p.endsWith(".config.ts") || p === "tsconfig.json"));
const isLocale: Covers = (p) =>
    p.startsWith("locale/") ||
    p.startsWith("web/xliff/") ||
    p.endsWith("locales.yaml") ||
    p === "scripts/locales.py";

/** `ci-lint-*` targets, run through make exactly as CI runs them. */
export const MAKE_JOBS: Record<string, Covers> = {
    "bandit": isPython,
    "black": isPython,
    "ruff": isPython,
    "mypy": isPython,
    "spellcheck": () => true,
    "catalogs": (p) =>
        ["package.json", "pnpm-workspace.yaml", "pnpm-lock.yaml"].includes(basename(p)),
    "locales": isLocale,
    "oxlint-fixtures": (p) => p.startsWith("packages/oxlint-config/"),
    "pending-migrations": (p) => p.startsWith("authentik/") && p.endsWith(".py"),
    "migrations": (p) => p.startsWith("authentik/") && p.includes("/migrations/"),
    "cargo-deny": isCargoManifest,
    "cargo-machete": isRust,
    "clippy": isRust,
    "rustfmt": (p) => p.endsWith(".rs"),
    "check-types": isNodeScript,
};

export interface Job {
    name: string;
    command: string[];
    covers: Covers;
    /** The workflow that runs it in CI. */
    ci: string;
}

export function jobs(): Job[] {
    const found: Job[] = Object.entries(MAKE_JOBS).map(([name, covers]) => ({
        name,
        command: ["make", `ci-lint-${name}`],
        covers,
        ci: "ci-main.yml",
    }));
    for (const script of ["lint:check", "tsc", "format:check", "lit-analyse"]) {
        found.push({
            name: `web-${script}`,
            command: ["pnpm", "--dir", "web", "run", script],
            covers: isWeb,
            ci: "ci-web.yml",
        });
    }
    found.push({
        name: "dev-mcp-check",
        command: ["pnpm", "--dir", "packages/dev-mcp", "run", "check"],
        covers: (p) => p.startsWith("packages/dev-mcp/"),
        ci: "none yet: no workflow runs workspace package checks",
    });
    found.push({
        name: "website-check",
        command: ["pnpm", "--dir", "website", "run", "check"],
        covers: (p) => p.startsWith("website/"),
        ci: "ci-docs.yml",
    });
    return found;
}

/** CI lint jobs this module doesn't know how to map. A drift test keeps this empty. */
export function unmappedJobs(): Set<string> {
    const all = new Set([...makefileLintTargets(), ...lintMatrix()]);
    for (const name of Object.keys(MAKE_JOBS)) all.delete(name);
    return all;
}

function ensurePlaceholders(): string[] {
    const created = [];
    for (const rel of CI_PLACEHOLDERS) {
        const path = join(ROOT, rel);
        if (existsSync(path)) continue;
        mkdirSync(dirname(path), { recursive: true });
        writeFileSync(path, "empty\n");
        created.push(rel);
    }
    return created;
}

async function fix(changed: string[], result: Result): Promise<void> {
    const steps: [string, boolean, string[][]][] = [
        [
            "python_rust",
            changed.some((p) => isPython(p) || p.endsWith(".rs")),
            [["make", "lint-fix"]],
        ],
        [
            "web",
            changed.some(isWeb),
            [
                ["pnpm", "--dir", "web", "run", "lint"],
                ["pnpm", "--dir", "web", "run", "format"],
            ],
        ],
        [
            "website",
            changed.some((p) => p.startsWith("website/")),
            [
                ["pnpm", "--dir", "website", "run", "lint"],
                ["pnpm", "--dir", "website", "run", "format"],
            ],
        ],
    ];
    const fixes: Record<string, unknown> = {};
    for (const [name, applies, commands] of steps) {
        if (!applies) continue;
        for (const [cmd, ...args] of commands) {
            const out = await run(cmd!, args, { timeoutMs: JOB_TIMEOUT });
            fixes[`${name}: ${[cmd, ...args].join(" ")}`] = {
                exit: out.code,
                output: tail(out, 1000),
            };
        }
    }
    result.data.fixes = fixes;
}

export async function lint(
    paths: string[] = [],
    base = DEFAULT_BASE,
    applyFixes = false,
): Promise<Result> {
    const result = new Result("akdev_lint");
    const changed = paths.length ? paths : changedFiles(base);
    if (!changed.length) {
        result.fingerprint = fingerprint();
        result.data.jobs = [];
        return result.finish(`No files changed since ${base}; nothing to lint`);
    }

    for (const name of [...unmappedJobs()].sort()) {
        result.skip(`ci-lint-${name}`, "no path rule for this job yet");
        result.command(`make ci-lint-${name}`);
    }
    if (!which("make")) result.unsure("make-based jobs", "make isn't on PATH");
    if (!which("pnpm")) result.unsure("web and docs jobs", "pnpm isn't on PATH");

    if (applyFixes) await fix(changed, result);
    const created = ensurePlaceholders();
    if (created.length) result.data.placeholdersCreated = created;

    const ran = [];
    for (const job of jobs()) {
        const files = changed.filter(job.covers);
        if (!files.length) continue;
        const [cmd, ...args] = job.command;
        const out = await run(cmd!, args, { timeoutMs: JOB_TIMEOUT });
        const command = job.command.join(" ");
        ran.push({
            job: job.name,
            command,
            ci: job.ci,
            ok: out.code === 0,
            exit: out.code,
            files: files.slice(0, 20),
            output: out.code === 0 ? "" : tail(out),
        });
        result.checked.push(job.name);
        if (out.code !== 0) {
            result.fail();
            result.command(command);
        }
    }

    const failed = ran.filter((r) => !r.ok).map((r) => r.job);
    result.data.jobs = ran;
    result.data.changedFiles = changed.length;
    // Fixes rewrite files, so fingerprint after them.
    result.fingerprint = fingerprint();
    return result.finish(
        `Ran ${ran.length} lint job(s) for ${changed.length} changed file(s): ` +
            (failed.length ? `${failed.length} failed (${failed.join(", ")})` : "all passed"),
    );
}
