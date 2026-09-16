/**
 * @file Post-processing for the generated client, run by `make build` before oxlint and oxfmt.
 *
 * The generator stamps `/* eslint-disable *\/` into every file it writes. ESLint no longer runs in
 * this repo, but oxlint honors the directive, and a file carrying it is a file oxlint will not
 * strip the generator's unused imports from. Removing it is what lets the fixer do that job.
 */

import { readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SOURCE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "src");

/** The exact line the generator emits, matched whole so a real directive elsewhere survives. */
const BANNER = "/* eslint-disable */";

/**
 * Yields every `.ts` file beneath `directory`.
 *
 * @param directory Absolute path to walk.
 *
 * @returns An async iterator of absolute file paths.
 */
async function* walk(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
        const path = join(directory, entry.name);

        if (entry.isDirectory()) {
            yield* walk(path);
        } else if (entry.name.endsWith(".ts")) {
            yield path;
        }
    }
}

let stripped = 0;

for await (const path of walk(SOURCE_ROOT)) {
    const source = await readFile(path, "utf-8");
    const next = source
        .split("\n")
        .filter((line) => line.trim() !== BANNER)
        .join("\n");

    if (next !== source) {
        await writeFile(path, next, "utf-8");
        stripped += 1;
    }
}

console.log(`✅  Removed the eslint-disable banner from ${stripped} generated files.`);
