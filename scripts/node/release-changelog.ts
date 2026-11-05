#!/usr/bin/env node
/**
 * @file Writes generated release notes into a release's partials under
 *   `website/docs/releases/<year>/v<year>.<minor>/`.
 *
 *   - `changelog` writes commits since the previous release into `_changelog.mdx`. A `.0` release
 *     replaces the list of minor changes; a patch release adds or replaces its own `## Fixed in
 *     <version>` section, so regenerating is idempotent.
 *   - `diff` writes the API schema diff against the previous release family into `_api-changes.mdx`.
 *     Usage: release-changelog <changelog|diff> --version <x.y.z>
 */

import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { parseArgs, promisify } from "node:util";

import { reportAndExit } from "./utils/commands.ts";
import { resolveRepoRoot } from "./utils/git.ts";
import { compareVersions } from "./utils/node.ts";

import { ConsoleLogger } from "#logger";

const logger = ConsoleLogger.prefix("release-changelog");

const execFileAsync = promisify(execFile);

async function run(file: string, args: string[], cwd: string): Promise<string> {
    const { stdout } = await execFileAsync(file, args, { cwd, maxBuffer: 64 * 1024 * 1024 });

    return stdout.trim();
}

//#region Releases

/**
 * The newest non-rc release tag older than the given version, without the `version/` prefix.
 */
async function previousRelease(version: string, cwd: string): Promise<string> {
    const tags = await run("git", ["tag", "--list", "version/*"], cwd);

    const previous = tags
        .split("\n")
        .map((tag) => tag.replace(/^version\//, ""))
        .filter((tag) => /^\d+\.\d+\.\d+$/.test(tag))
        .filter((tag) => compareVersions(tag, version) < 0)
        .sort(compareVersions)
        .at(-1);

    if (!previous) {
        throw new Error(`No release found before ${version}`);
    }

    return previous;
}

function partialPath(root: string, version: string, name: string): string {
    const [year, minor] = version.split(".");

    return join(root, "website/docs/releases", year!, `v${year}.${minor}`, `_${name}.mdx`);
}

//#endregion

//#region Changelog

const PATCH_HEADING = /^## Fixed in (\S+)\s*$/m;
const CHERRY_PICK = /cherry-pick (#\d+)/g;
const EXCLUDED_ENTRY = /^- (ci:|website)/;

interface ChangelogPartial {
    minorChanges: string;
    patches: Map<string, string>;
}

function parsePartial(content: string): ChangelogPartial {
    const [minorChanges = "", ...rest] = content.split(PATCH_HEADING);
    const patches = new Map<string, string>();

    for (let i = 0; i < rest.length; i += 2) {
        const [version, entries = ""] = rest.slice(i, i + 2);

        if (version) patches.set(version, entries.trim());
    }

    return { minorChanges: minorChanges.trim(), patches };
}

function renderPartial({ minorChanges, patches }: ChangelogPartial): string {
    const sections = [...patches.entries()]
        .sort(([left], [right]) => compareVersions(left, right))
        .map(([version, entries]) => `## Fixed in ${version}\n\n${entries}`);

    return [minorChanges, ...sections].filter(Boolean).join("\n\n") + "\n";
}

async function commitSubjects(range: string, cwd: string): Promise<string[]> {
    const output = await run("git", ["log", "--pretty=format:- %s", range], cwd);

    return output ? output.split("\n") : [];
}

/**
 * Commits since the previous release, minus those already cherry-picked onto it.
 * These are best-effort guesses based on commit messages.
 */
async function collectEntries(previousTag: string, cwd: string): Promise<string> {
    const base = await run("git", ["merge-base", previousTag, "HEAD"], cwd);

    const [current, previous] = await Promise.all([
        commitSubjects(`${base}...HEAD`, cwd),
        commitSubjects(`${base}...${previousTag}`, cwd),
    ]);

    const cherryPicked = new Set(
        previous.flatMap((line) => [...line.matchAll(CHERRY_PICK)].map(([, pr]) => `(${pr})`)),
    );

    return current
        .filter((line) => ![...cherryPicked].some((suffix) => line.endsWith(suffix)))
        .filter((line) => !EXCLUDED_ENTRY.test(line))
        .sort()
        .join("\n");
}

async function writeChangelog(version: string, root: string): Promise<string> {
    const previousTag = `version/${await previousRelease(version, root)}`;
    const entries = await collectEntries(previousTag, root);

    if (!entries) {
        throw new Error(`No changelog entries found since ${previousTag}`);
    }

    const output = partialPath(root, version, "changelog");

    const partial = existsSync(output)
        ? parsePartial(await readFile(output, "utf-8"))
        : { minorChanges: "", patches: new Map<string, string>() };

    if (version.endsWith(".0")) {
        partial.minorChanges = entries;
    } else {
        partial.patches.set(version, entries);
    }

    await mkdir(dirname(output), { recursive: true });
    await writeFile(output, renderPartial(partial));

    return output;
}

//#endregion

//#region API diff

async function writeDiff(version: string, root: string): Promise<string> {
    const [year, minor] = version.split(".");
    const previousTag = `version/${await previousRelease(`${year}.${minor}.0`, root)}`;

    const oldSchema = join(root, "schema-old.yml");
    const diffPath = join(root, "diff.md");

    try {
        await writeFile(oldSchema, await run("git", ["show", `${previousTag}:schema.yml`], root));

        await run(
            "docker",
            [
                "compose",
                "-f",
                "scripts/compose.yml",
                "run",
                "--rm",
                "--user",
                `${process.getuid?.()}:${process.getgid?.()}`,
                "diff",
                "--markdown",
                "/local/diff.md",
                "/local/schema-old.yml",
                "/local/schema.yml",
            ],
            root,
        );

        const diff = (await readFile(diffPath, "utf-8"))
            .replaceAll("{", "&#123;")
            .replaceAll("}", "&#125;");

        const output = partialPath(root, version, "api-changes");

        await mkdir(dirname(output), { recursive: true });
        await writeFile(output, diff);

        return output;
    } finally {
        await rm(oldSchema, { force: true });
        await rm(diffPath, { force: true });
    }
}

//#endregion

const COMMANDS = {
    changelog: writeChangelog,
    diff: writeDiff,
} as const;

async function main(): Promise<void> {
    const { values, positionals } = parseArgs({
        options: { version: { type: "string" } },
        allowPositionals: true,
    });

    const [command] = positionals;
    const { version } = values;

    if (!command || !(command in COMMANDS)) {
        throw new Error("Usage: release-changelog <changelog|diff> --version <x.y.z>");
    }

    if (!version || !/^\d+\.\d+\.\d+$/.test(version)) {
        throw new Error("Pass the release with --version, e.g. --version 2026.11.0");
    }

    const root = await resolveRepoRoot();
    const output = await COMMANDS[command as keyof typeof COMMANDS](version, root);

    await run("pnpm", ["exec", "oxfmt", "--write", output], root);

    logger.info(`✅ Wrote the ${version} ${command} to ${output}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => reportAndExit(error, logger));
