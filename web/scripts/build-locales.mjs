/**
 * @file Lit Localize build script.
 *
 * @import { Config } from "@lit/localize-tools/lib/types/config.js"
 */
import * as fs from "node:fs/promises";
import * as path from "node:path";
import process from "node:process";
import { $ } from "zx";

const localizeRules = await import("../lit-localize.json", {
    with: {
        type: "json",
    },
})
    .then((module) => {
        return /** @type {Config} */ (module.default);
    })

    .catch((error) => {
        console.error("Failed to load lit-localize.json", error);
        process.exit(1);
    });

/**
 * Attempt to stat a file, returning null if it doesn't exist.
 */
function tryStat(filePath) {
    return fs.stat(filePath).catch(() => null);
}

/**
 * Check if a generated file is up-to-date with its XLIFF source.
 *
 * @param {string} languageCode The locale to check.
 */
async function generatedFileIsUpToDateWithXliffSource(languageCode) {
    const xlfFilePath = path.join("./xliff", `${languageCode}.xlf`);
    const xlfStat = await tryStat(xlfFilePath);

    if (!xlfStat) {
        console.error(`lit-localize expected '${languageCode}.xlf', but XLF file is not present`);

        process.exit(1);
    }

    const generatedTSFilePath = path.join("./src/locales", `${languageCode}.ts`);

    const generatedTSFilePathStat = await tryStat(generatedTSFilePath);

    // Does the generated file exist?
    if (!generatedTSFilePathStat) {
        return {
            languageCode,
            exists: false,
            expired: null,
        };
    }

    return {
        languageCode,
        exists: true,
        // Is the generated file older than the XLIFF file?
        expired: generatedTSFilePathStat.mtimeMs < xlfStat.mtimeMs,
    };
}

const results = await Promise.all(
    localizeRules.targetLocales.map(generatedFileIsUpToDateWithXliffSource),
);

const pendingBuild = results.some((result) => !result.exists || result.expired);

if (!pendingBuild) {
    console.log("Local is up-to-date!");
    process.exit(0);
}

const status = await $({ stdio: ["ignore", "pipe", "pipe"] })`npx lit-localize build`;

/**
 * @type {Map<string, number>}
 */
const counts = new Map();

// Count all the missing message warnings
for (const line of status.stderr.split("\n")) {
    const match = /^([\w-]+) message/.exec(line);
    if (!match) continue;

    const count = counts.get(match[1]) || 0;
    counts.set(match[1], count + 1);
}

const locales = Array.from(counts.keys()).sort();

for (const locale of locales) {
    console.log(`Locale '${locale}' has ${counts.get(locale)} missing translations`);
}

await $`npx prettier --write src/locale-codes.ts`;

console.log("\nTranslation tables rebuilt.\n");
