/**
 * @file Fixture verification for the bundled oxlint plugin. Runs oxlint over deliberately-violating
 *   fixtures and asserts each padding rule fires — and only where expected. The rules ship as
 *   autofixes that rewrite source, so "fires where expected" is not enough on its own: this also
 *   runs `--fix` over a copy of each violating fixture and checks the result equals the matching
 *   `clean` fixture. That is what proves the fix converges instead of inserting a second blank line
 *   on the next pass. Stands in for a test runner, which this package does not otherwise need.
 */

import { execFileSync } from "node:child_process";
import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createOxlintConfig } from "../out/index.js";

const require = createRequire(import.meta.url);
const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

// Resolve the oxlint binary regardless of PATH.
const oxlintPackageJson = require.resolve("oxlint/package.json");
const oxlintPackage = JSON.parse(readFileSync(oxlintPackageJson, "utf8"));
const binRelative =
    typeof oxlintPackage.bin === "string" ? oxlintPackage.bin : oxlintPackage.bin.oxlint;
const oxlintBin = resolve(dirname(oxlintPackageJson), binRelative);

// Build the config from the factory, with the padding rules switched on and `fixtures/` reachable.
// The shipped config ignores `fixtures/**`, which would switch off the very rules under test.
const configPath = resolve(packageRoot, ".oxlintrc.generated.json");

writeFileSync(
    configPath,
    JSON.stringify(
        createOxlintConfig({
            padding: true,
            ignorePatterns: ["**/node_modules", "**/out", "**/dist"],
        }),
        null,
        1,
    ),
);

/** Every fixture, paired with the rule it exercises and whether it should be flagged. */
const expectations = [
    { file: "fixtures/padding/needs-padding.ts", rule: "padding-lines", expect: true },
    { file: "fixtures/padding/clean.ts", rule: "padding-lines", expect: false },
    { file: "fixtures/padding/ts-declarations.ts", rule: "padding-lines", expect: true },
    { file: "fixtures/padding/ts-declarations-clean.ts", rule: "padding-lines", expect: false },
    { file: "fixtures/console/needs-padding.ts", rule: "console-padding", expect: true },
    // A run of calls is one group, and a call that opens a block needs nothing before it.
    { file: "fixtures/console/clean.ts", rule: "console-padding", expect: false },
    {
        file: "fixtures/multiline/needs-padding.ts",
        rule: "multiline-statement-padding",
        expect: true,
    },
    { file: "fixtures/multiline/clean.ts", rule: "multiline-statement-padding", expect: false },
    // Statements on one line cannot be separated by a blank line; asking is asking the impossible.
    { file: "fixtures/multiline/asi-guard.ts", rule: "padding-lines", expect: false },
    { file: "fixtures/multiline/asi-guard.ts", rule: "multiline-statement-padding", expect: false },
];

/** Violating fixtures paired with the formatted result their autofix must produce. */
const fixPairs = [
    ["fixtures/padding/needs-padding.ts", "fixtures/padding/clean.ts"],
    ["fixtures/padding/ts-declarations.ts", "fixtures/padding/ts-declarations-clean.ts"],
    ["fixtures/multiline/needs-padding.ts", "fixtures/multiline/clean.ts"],
];

const files = [...new Set(expectations.map(({ file }) => file))];

let stdout;

try {
    stdout = execFileSync(
        process.execPath,
        [oxlintBin, "-c", configPath, "--format", "json", ...files],
        { cwd: packageRoot, encoding: "utf8" },
    );
} catch (error) {
    // oxlint exits non-zero on error-severity diagnostics; these rules are warnings, but be safe.
    stdout = error.stdout ?? "";
}

const { diagnostics } = JSON.parse(stdout);

const flaggedBy = (rule) =>
    new Set(
        diagnostics
            .filter((diagnostic) => diagnostic.code.includes(rule))
            .map((diagnostic) => diagnostic.filename.replaceAll("\\", "/")),
    );

const failures = [];

for (const { file, rule, expect } of expectations) {
    const found = [...flaggedBy(rule)].some((flagged) => flagged.endsWith(file));

    if (expect && !found) {
        failures.push(`expected a ${rule} violation in ${file}, found none`);
    }

    if (!expect && found) {
        failures.push(`unexpected ${rule} violation in ${file}`);
    }
}

// The autofix must land the file exactly on its `clean` counterpart, and a second pass must change
// nothing further — a fix anchored to the wrong end inserts another blank line every run.
const workspace = mkdtempSync(join(tmpdir(), "ak-oxlint-fixtures-"));

try {
    for (const [violating, clean] of fixPairs) {
        const scratch = join(workspace, violating.replaceAll("/", "-"));

        copyFileSync(resolve(packageRoot, violating), scratch);

        for (const pass of [1, 2]) {
            try {
                execFileSync(process.execPath, [oxlintBin, "-c", configPath, "--fix", scratch], {
                    cwd: packageRoot,
                });
            } catch {
                // `--fix` may exit non-zero; the file contents are what is asserted.
            }

            const fixed = readFileSync(scratch, "utf8");
            const expected = readFileSync(resolve(packageRoot, clean), "utf8");

            if (fixed !== expected) {
                failures.push(
                    `autofix pass ${pass} of ${violating} did not produce ${clean}:\n` +
                        `--- got ---\n${fixed}--- want ---\n${expected}`,
                );

                break;
            }
        }
    }
} finally {
    rmSync(workspace, { recursive: true, force: true });
}

// The rules must stay off unless a consumer asks for them: they rewrite source, and switching them
// on by default would reformat every repo that upgrades this package.
const defaults = createOxlintConfig().rules;

for (const rule of ["padding-lines", "console-padding", "multiline-statement-padding"]) {
    if (defaults[`goauthentik/${rule}`]) {
        failures.push(`${rule} is enabled by default — it must be opt-in via \`padding\``);
    }
}

const enabled = createOxlintConfig({ padding: true }).rules;

for (const rule of ["padding-lines", "console-padding", "multiline-statement-padding"]) {
    if (!enabled[`goauthentik/${rule}`]) {
        failures.push(`${rule} is missing when \`padding\` is on`);
    }
}

rmSync(configPath, { force: true });

if (failures.length) {
    console.error("fixtures FAILED:");

    for (const failure of failures) {
        console.error("  - " + failure);
    }

    process.exit(1);
}

console.log(
    `fixtures OK (${flaggedBy("padding-lines").size} padding-lines + ` +
        `${flaggedBy("console-padding").size} console-padding + ` +
        `${flaggedBy("multiline-statement-padding").size} multiline-statement-padding ` +
        `violations, ${fixPairs.length} autofixes converged)`,
);
