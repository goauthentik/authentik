#!/usr/bin/env node
/**
 * @file Writes generated release notes into a release's partials under
 *   `website/docs/releases/<year>/v<year>.<minor>/`.
 *
 *   - `changelog` writes commits since the previous release into `_changelog.mdx`. A `.0` release
 *     replaces the list of minor changes; a patch release adds or replaces its own `## Fixed in
 *     <version>` section, so regenerating is idempotent.
 *   - `diff` writes the API schema diff against the previous release family into `_api-changes.mdx`.
 *     Run it from the release branch (`version-<year>.<minor>`); other branches yield the wrong
 *     commits. `--review` prints the result instead of writing it.
 *
 * @example
 *     ```sh
 *     release-changelog <changelog|diff> --version <x.y.z> [--review]
 *     ```;
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

import type { List, ListItem, Nodes, PhrasingContent } from "mdast";
import { fromMarkdown } from "mdast-util-from-markdown";
import { mdxToMarkdown } from "mdast-util-mdx";
import { type Options as ToMarkdownOptions, toMarkdown } from "mdast-util-to-markdown";

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

/**
 * Fails unless HEAD is the release branch for the given version.
 */
async function assertReleaseBranch(version: string, cwd: string): Promise<void> {
    const [year, minor] = version.split(".");
    const expected = `version-${year}.${minor}`;
    const branch = await run("git", ["rev-parse", "--abbrev-ref", "HEAD"], cwd);

    if (branch !== expected) {
        throw new Error(
            `Check out ${expected} before generating ${version} (on ${branch}). Pass --review to preview anyway.`,
        );
    }
}

interface Generated {
    output: string;
    content: string;
}

//#endregion

//#region Changelog

const PATCH_HEADING = /^## Fixed in (\S+)\s*$/m;
const CHERRY_PICK = /cherry-pick (#\d+)/g;
const EXCLUDED_ENTRY = /^- (ci:|website)/;
const KEPT_ENTRY = /^- security:/;
const BUMP_ENTRY = /^- (revert: )?([^:]+: )?bump /i;
const TRANSLATION_ENTRY =
    /^- (translate: Updates for project authentik and language (?<locale>\S+)|core, web: update translations) \(#\d+\)$/;
const PULL_REQUEST_SUFFIX = / \((#\d+)\)$/;
const DIFF_VERSION_HEADING = /^(#+ authentik \(v )\S+\)/m;

interface ChangelogPartial {
    minorChanges: string;
    patches: Map<string, string>;
}

function parsePartial(content: string): ChangelogPartial {
    const [minorChanges = "", ...rest] = content.split(PATCH_HEADING);
    const patches = new Map<string, string>();

    for (let i = 0; i < rest.length; i += 2) {
        const [version, entries = ""] = rest.slice(i, i + 2);

        if (version) {
            patches.set(version, entries.trim());
        }
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

    const entries = current
        .filter((line) => ![...cherryPicked].some((suffix) => line.endsWith(suffix)))
        .filter((line) => !EXCLUDED_ENTRY.test(line))
        .filter((line) => KEPT_ENTRY.test(line) || !BUMP_ENTRY.test(line));

    const sorted = mergeDuplicates(summarizeTranslations(entries)).sort((left, right) =>
        left.localeCompare(right, "en", { sensitivity: "base" }),
    );

    return sorted.length ? renderEntries(sorted) : "";
}

/**
 * Replaces the per-locale Transifex and extraction commits with one entry listing the locales.
 */
function summarizeTranslations(entries: string[]): string[] {
    const locales = new Set<string>();
    let summarized = false;

    const rest = entries.filter((line) => {
        const match = TRANSLATION_ENTRY.exec(line);

        if (!match) return true;

        summarized = true;

        if (match.groups?.locale) {
            locales.add(match.groups.locale);
        }

        return false;
    });

    if (!summarized) {
        return rest;
    }

    const languages = locales.size ? ` for ${[...locales].sort().join(", ")}` : "";

    return [...rest, `- translate: update translations${languages}`];
}

/**
 * Collapses entries with the same subject into one, listing every pull request.
 */
function mergeDuplicates(entries: string[]): string[] {
    const merged = new Map<string, string[]>();

    for (const line of entries) {
        const [, pullRequest] = PULL_REQUEST_SUFFIX.exec(line) ?? [];
        const subject = line.replace(PULL_REQUEST_SUFFIX, "");
        const pullRequests = merged.get(subject) ?? [];

        if (pullRequest) pullRequests.push(pullRequest);

        merged.set(subject, pullRequests);
    }

    return [...merged].map(([subject, pullRequests]) =>
        pullRequests.length ? `${subject} (${pullRequests.sort().join(", ")})` : subject,
    );
}

const MARKDOWN_OPTIONS: ToMarkdownOptions = {
    bullet: "-",
    rule: "-",
    extensions: [mdxToMarkdown()],
};

/**
 * Turns raw HTML into text, so the serializer escapes it rather than passing it through as markup.
 */
function textifyHTML(node: Nodes): Nodes {
    if (node.type === "html") {
        return { type: "text", value: node.value };
    }

    if ("children" in node) {
        node.children = node.children.map(textifyHTML) as typeof node.children;
    }

    return node;
}

/**
 * Splits a commit subject into text and inline code, so backticked spans stay verbatim.
 */
function toPhrasing(subject: string): PhrasingContent[] {
    const segments = subject.split("`");

    if (segments.length % 2 === 0) {
        const unmatched = segments.pop();
        segments[segments.length - 1] += `\`${unmatched}`;
    }

    return segments.flatMap((value, index): PhrasingContent[] => {
        if (!value) return [];

        return [index % 2 ? { type: "inlineCode", value } : { type: "text", value }];
    });
}

/**
 * Serializes entries as an MDX list, escaping anything MDX would read as markup.
 */
function renderEntries(entries: string[]): string {
    const list: List = {
        type: "list",
        ordered: false,
        spread: false,
        children: entries.map((line): ListItem => ({
            type: "listItem",
            spread: false,
            children: [{ type: "paragraph", children: toPhrasing(line.replace(/^- /, "")) }],
        })),
    };

    return toMarkdown(list, MARKDOWN_OPTIONS).trim();
}

async function generateChangelog(version: string, root: string): Promise<Generated> {
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

    return { output, content: renderPartial(partial) };
}

//#endregion

//#region API diff

async function generateDiff(version: string, root: string): Promise<Generated> {
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

        const source = (await readFile(diffPath, "utf-8")).replace(
            DIFF_VERSION_HEADING,
            `$1${version})`,
        );

        const diff = toMarkdown(textifyHTML(fromMarkdown(source)), MARKDOWN_OPTIONS);

        return { output: partialPath(root, version, "api-changes"), content: diff };
    } finally {
        await rm(oldSchema, { force: true });
        await rm(diffPath, { force: true });
    }
}

//#endregion

const COMMANDS = {
    changelog: generateChangelog,
    diff: generateDiff,
} as const;

async function main(): Promise<void> {
    const { values, positionals } = parseArgs({
        options: { version: { type: "string" }, review: { type: "boolean", default: false } },
        allowPositionals: true,
    });

    const [command] = positionals;
    const { version, review } = values;

    if (!command || !(command in COMMANDS)) {
        throw new Error("Usage: release-changelog <changelog|diff> --version <x.y.z> [--review]");
    }

    if (!version || !/^\d+\.\d+\.\d+$/.test(version)) {
        throw new Error("Pass the release with --version, e.g. --version 2026.11.0");
    }

    const root = await resolveRepoRoot();

    if (!review) await assertReleaseBranch(version, root);

    const { output, content } = await COMMANDS[command as keyof typeof COMMANDS](version, root);

    if (review) {
        process.stdout.write(content);
        return;
    }

    await mkdir(dirname(output), { recursive: true });
    await writeFile(output, content);
    await run("pnpm", ["exec", "oxfmt", "--write", output], root);

    logger.info(`✅ Wrote the ${version} ${command} to ${output}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => reportAndExit(error, logger));
