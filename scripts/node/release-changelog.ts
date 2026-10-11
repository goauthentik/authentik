#!/usr/bin/env node
/**
 * @file Writes generated changelog entries into a release's changelog partial. A `.0` release
 *   replaces the list of minor changes; a patch release adds or replaces its own
 *   `## Fixed in <version>` section, so regenerating is idempotent. Usage: release-changelog
 *   --version <x.y.z> --output <partial.mdx> <entries.md>
 */

import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { parseArgs } from "node:util";

import { reportAndExit } from "./utils/commands.ts";
import { compareVersions } from "./utils/node.ts";

import { ConsoleLogger } from "#logger";

const logger = ConsoleLogger.prefix("release-changelog");

const PATCH_HEADING = /^## Fixed in (\S+)\s*$/m;

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

async function main(): Promise<void> {
    const { values, positionals } = parseArgs({
        options: {
            version: { type: "string" },
            output: { type: "string" },
        },
        allowPositionals: true,
    });

    const { version, output } = values;
    const [inputPath] = positionals;

    if (!version || !/^\d+\.\d+\.\d+$/.test(version)) {
        throw new Error("Pass the release with --version, e.g. --version 2026.11.0");
    }

    if (!output || !inputPath) {
        throw new Error("Usage: release-changelog --version <x.y.z> --output <partial.mdx> <entries.md>");
    }

    const entries = (await readFile(inputPath, "utf-8")).trim();

    if (!entries) {
        throw new Error(`No changelog entries found in ${inputPath}`);
    }

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

    logger.info(`✅ Wrote the ${version} changelog to ${output}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => reportAndExit(error, logger));
