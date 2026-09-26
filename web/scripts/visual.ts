import { execFileSync, spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import * as fs from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, relative, resolve } from "node:path";
import { parseArgs } from "node:util";

import {
    commitDirectory,
    PlatformKey,
    reportDirectory,
    suiteDirectory,
    type VisualSuite,
    VisualSuites,
} from "../test/visual/environment.ts";

import { ConsoleLogger } from "#logger/node";
import { PackageRoot } from "#paths/node";

const logger = ConsoleLogger.child({ name: "Visual" });
const require = createRequire(import.meta.url);

const ConfigPath = resolve(PackageRoot, "playwright.visual.config.ts");
const SpecDirectory = resolve(PackageRoot, "test", "visual");
const PlaywrightVersion: string = require("@playwright/test/package.json").version;

//#region CLI

const HelpText = `
Usage: pnpm run test:visual -- [suite...] [options] [-- <playwright args>]

Suites:
  storybook   Every story in a Storybook build (default)
  pages       Admin pages on the running instance at AK_TEST_RUNNER_PAGE_URL

Options:
  --base <ref>        Branch to compare against (default: $AK_VISUAL_BASE or origin/main).
                      The baseline is the merge-base of HEAD and this ref.
  --record            Record HEAD as a baseline instead of comparing. Needs a clean tree.
  --rebuild-baseline  Discard the cached baseline and record it again.
  --skip-build        Reuse the existing storybook-static instead of rebuilding.
  --keep-worktree     Keep the baseline's git worktree around after recording it.
  -h, --help          Show this message.
`;

// pnpm forwards the `--` in `pnpm run test:visual -- …`.
const argv = process.argv[2] === "--" ? process.argv.slice(3) : process.argv.slice(2);
const separator = argv.indexOf("--");
const ownArgs = separator === -1 ? argv : argv.slice(0, separator);
const playwrightArgs = separator === -1 ? [] : argv.slice(separator + 1);

const { values: options, positionals } = parseArgs({
    args: ownArgs,
    allowPositionals: true,
    options: {
        "base": { type: "string", default: process.env.AK_VISUAL_BASE || "origin/main" },
        "record": { type: "boolean", default: false },
        "rebuild-baseline": { type: "boolean", default: false },
        "skip-build": { type: "boolean", default: false },
        "keep-worktree": { type: "boolean", default: false },
        "help": { type: "boolean", short: "h", default: false },
    },
});

function isSuite(value: string): value is VisualSuite {
    return (VisualSuites as readonly string[]).includes(value);
}

//#endregion

//#region Processes

function git(...args: string[]): string {
    return execFileSync("git", args, { cwd: PackageRoot, encoding: "utf8" }).trim();
}

function run(
    command: string,
    args: string[],
    { cwd = PackageRoot, env = {} }: { cwd?: string; env?: Record<string, string> } = {},
): Promise<number> {
    logger.debug(`${relative(PackageRoot, cwd) || "."}$ ${command} ${args.join(" ")}`);

    return new Promise((resolvePromise, reject) => {
        const child = spawn(command, args, {
            cwd,
            stdio: "inherit",
            env: { ...process.env, ...env },
        });

        child.once("error", reject);
        child.once("exit", (code, signal) => resolvePromise(code ?? (signal ? 1 : 0)));
    });
}

async function runOrThrow(...params: Parameters<typeof run>): Promise<void> {
    const code = await run(...params);

    if (code !== 0) {
        throw new Error(`\`${params[0]} ${params[1].join(" ")}\` exited with ${code}`);
    }
}

//#endregion

//#region Baselines

interface BaselineManifest {
    suite: VisualSuite;
    commit: string;
    platform: string;
    playwright: string;
    specHash: string;
    recordedAt: string;
}

async function hashSpecs(): Promise<string> {
    const hash = createHash("sha256");

    const files = (await fs.readdir(SpecDirectory))
        .filter((name) => name.endsWith(".ts"))
        .sort()
        .map((name) => join(SpecDirectory, name));

    for (const file of [ConfigPath, ...files]) {
        hash.update(relative(PackageRoot, file));
        hash.update(await fs.readFile(file));
    }

    return hash.digest("hex").slice(0, 16);
}

async function readManifest(commit: string, suite: VisualSuite): Promise<BaselineManifest | null> {
    try {
        const raw = await fs.readFile(join(suiteDirectory(commit, suite), "manifest.json"), "utf8");

        return JSON.parse(raw);
    } catch {
        return null;
    }
}

function staleReason(manifest: BaselineManifest | null, specHash: string): string | null {
    if (!manifest) return "no baseline recorded";

    if (manifest.specHash !== specHash) return "the visual specs changed since it was recorded";

    if (manifest.playwright !== PlaywrightVersion) {
        return `it was recorded with Playwright ${manifest.playwright}`;
    }

    return null;
}

async function writeManifest(commit: string, suite: VisualSuite, specHash: string): Promise<void> {
    const manifest: BaselineManifest = {
        suite,
        commit,
        platform: PlatformKey,
        playwright: PlaywrightVersion,
        specHash,
        recordedAt: new Date().toISOString(),
    };

    await fs.writeFile(
        join(suiteDirectory(commit, suite), "manifest.json"),
        JSON.stringify(manifest, null, 4) + "\n",
    );
}

//#endregion

//#region Playwright

interface PlaywrightRun {
    suite: VisualSuite;
    commit: string;
    mode: "record" | "compare";
    storybookDirectory?: string;
}

function runPlaywright({
    suite,
    commit,
    mode,
    storybookDirectory,
}: PlaywrightRun): Promise<number> {
    const env: Record<string, string> = {
        AK_VISUAL_BASELINE_DIR: commitDirectory(commit),
        AK_VISUAL_SUITE: suite,
    };

    if (storybookDirectory) env.AK_VISUAL_STORYBOOK_DIR = storybookDirectory;

    return run(
        "pnpm",
        [
            "exec",
            "playwright",
            "test",
            "--config",
            ConfigPath,
            "--project",
            suite,
            `--update-snapshots=${mode === "record" ? "all" : "none"}`,
            ...playwrightArgs,
        ],
        { env },
    );
}

async function buildStorybook(cwd: string): Promise<string> {
    logger.info(`Building Storybook in ${cwd === PackageRoot ? "the working tree" : cwd}`);

    // Older commits' `storybook:build` doesn't build locales.
    if (cwd !== PackageRoot) {
        await runOrThrow("pnpm", ["run", "build-locales"], { cwd });
    }

    await runOrThrow("pnpm", ["run", "storybook:build"], { cwd });

    return join(cwd, "storybook-static");
}

async function record(
    suite: VisualSuite,
    commit: string,
    specHash: string,
    storybookDirectory?: string,
): Promise<void> {
    await fs.rm(suiteDirectory(commit, suite), { recursive: true, force: true });
    await fs.mkdir(suiteDirectory(commit, suite), { recursive: true });

    const code = await runPlaywright({ suite, commit, mode: "record", storybookDirectory });

    if (code !== 0) {
        logger.warn(
            `Some ${suite} screenshots failed to record for ${commit.slice(0, 10)}; they'll be reported as new.`,
        );
    }

    await writeManifest(commit, suite, specHash);
}

async function recordStorybookFromWorktree(commit: string, specHash: string): Promise<void> {
    const worktree = join(tmpdir(), `authentik-visual-${commit.slice(0, 12)}`);
    const worktreeWeb = join(worktree, relative(git("rev-parse", "--show-toplevel"), PackageRoot));

    if (!existsSync(worktree)) {
        logger.info(`Checking out ${commit.slice(0, 10)} into ${worktree}`);
        git("worktree", "add", "--detach", worktree, commit);
    }

    try {
        logger.info("Installing the baseline's dependencies");
        await runOrThrow("pnpm", ["install", "--frozen-lockfile"], { cwd: worktreeWeb });

        const storybookDirectory = await buildStorybook(worktreeWeb);

        await record("storybook", commit, specHash, storybookDirectory);
    } finally {
        if (options["keep-worktree"]) {
            logger.info(`Kept the worktree at ${worktree}`);
        } else {
            git("worktree", "remove", "--force", worktree);
        }
    }
}

//#endregion

//#region Commands

interface Revisions {
    head: string;
    dirty: boolean;
}

function readRevisions(): Revisions {
    return {
        head: git("rev-parse", "HEAD"),
        dirty: git("status", "--porcelain").length > 0,
    };
}

async function recordHead(suite: VisualSuite, { head, dirty }: Revisions, specHash: string) {
    if (dirty) {
        throw new Error(
            "Baselines are keyed by commit, so --record needs a clean tree. Commit or stash first.",
        );
    }

    logger.info(`Recording ${suite} for ${head.slice(0, 10)} (${PlatformKey})`);

    const storybookDirectory =
        suite === "storybook" && !options["skip-build"]
            ? await buildStorybook(PackageRoot)
            : undefined;

    await record(suite, head, specHash, storybookDirectory);

    logger.info(`Saved to ${relative(PackageRoot, suiteDirectory(head, suite))}`);
}

async function ensureBaseline(
    suite: VisualSuite,
    base: string,
    { head, dirty }: Revisions,
    specHash: string,
): Promise<void> {
    const reason = options["rebuild-baseline"]
        ? "--rebuild-baseline was passed"
        : staleReason(await readManifest(base, suite), specHash);

    if (!reason) {
        logger.info(`Using the cached ${suite} baseline for ${base.slice(0, 10)}`);

        return;
    }

    logger.info(`Recording a ${suite} baseline for ${base.slice(0, 10)}: ${reason}`);

    if (suite === "pages") {
        throw new Error(
            [
                `No usable pages baseline for ${base.slice(0, 10)} (${reason}). To record one:`,
                `  git switch --detach ${base}`,
                "  make dev-reset && make run            # in another terminal",
                "  pnpm run test:visual -- pages --record",
                "  git switch -                          # then compare again",
            ].join("\n"),
        );
    }

    if (base === head && !dirty) {
        await record(suite, base, specHash, await buildStorybook(PackageRoot));
    } else {
        await recordStorybookFromWorktree(base, specHash);
    }
}

async function compare(suite: VisualSuite, revisions: Revisions, specHash: string) {
    const baseRef = options.base!;
    const base = git("merge-base", "HEAD", baseRef);

    logger.info(
        `Comparing ${suite}: ${revisions.dirty ? "working tree" : revisions.head.slice(0, 10)}` +
            ` against ${base.slice(0, 10)} (merge-base with ${baseRef})`,
    );

    if (base === revisions.head && !revisions.dirty) {
        logger.warn(`HEAD is the merge-base with ${baseRef}; this only checks for flakiness.`);
    }

    await ensureBaseline(suite, base, revisions, specHash);

    const storybookDirectory =
        suite === "storybook"
            ? options["skip-build"]
                ? join(PackageRoot, "storybook-static")
                : await buildStorybook(PackageRoot)
            : undefined;

    const code = await runPlaywright({ suite, commit: base, mode: "compare", storybookDirectory });

    logger.info(
        `Report: pnpm exec playwright show-report ${relative(PackageRoot, reportDirectory(suite))}`,
    );

    return code;
}

//#endregion

async function main(): Promise<number> {
    if (options.help) {
        console.log(HelpText.trim());

        return 0;
    }

    const unknown = positionals.filter((value) => !isSuite(value));

    if (unknown.length) {
        throw new Error(`Unknown suite: ${unknown.join(", ")}. Expected one of: ${VisualSuites}`);
    }

    const suites = positionals.length ? (positionals as VisualSuite[]) : ["storybook" as const];
    const revisions = readRevisions();
    const specHash = await hashSpecs();

    let exitCode = 0;

    for (const suite of suites) {
        if (options.record) {
            await recordHead(suite, revisions, specHash);
        } else {
            exitCode ||= await compare(suite, revisions, specHash);
        }
    }

    return exitCode;
}

main()
    .then((code) => process.exit(code))
    .catch((error: unknown) => {
        logger.error(error instanceof Error ? error.message : error);
        process.exit(1);
    });
