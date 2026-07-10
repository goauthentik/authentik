#!/usr/bin/env node
/**
 * @file Rewrites `web/package.json` in place for a public npm publish.
 *
 * Consumers install `@goauthentik/web` as source; the workspace-only bits — the
 * `link:` fallback for the local prettier config, the `link:` reference to the
 * generated `@goauthentik/api` client, and the internal placeholder version —
 * need real values that resolve outside the monorepo.
 *
 * Called from the release workflow before `pnpm publish`. Idempotent.
 *
 * Usage:
 *   node scripts/prepare-publish.mjs --version 2026.8.0 [--api-version 2026.8.0]
 */
import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const HERE = dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = resolve(HERE, "..");
const MANIFEST_PATH = resolve(WEB_ROOT, "package.json");

const { values } = parseArgs({
    options: {
        "version": { type: "string" },
        "api-version": { type: "string" },
    },
});

if (!values.version) {
    console.error("prepare-publish: --version <semver> is required");
    process.exit(2);
}

const releaseVersion = values.version.replace(/^v/, "");
const apiVersion = (values["api-version"] || releaseVersion).replace(/^v/, "");

const manifest = JSON.parse(await readFile(MANIFEST_PATH, "utf8"));

manifest.version = releaseVersion;

if (manifest.dependencies?.["@goauthentik/api"]?.startsWith("link:")) {
    manifest.dependencies["@goauthentik/api"] = `^${apiVersion}`;
}

if (manifest.optionalDependencies) {
    for (const [name, spec] of Object.entries(manifest.optionalDependencies)) {
        if (typeof spec === "string" && (spec.startsWith("link:") || spec.startsWith("file:"))) {
            delete manifest.optionalDependencies[name];
        }
    }
    if (Object.keys(manifest.optionalDependencies).length === 0) {
        delete manifest.optionalDependencies;
    }
}

await writeFile(MANIFEST_PATH, `${JSON.stringify(manifest, null, 4)}\n`);

console.log(`prepare-publish: web/package.json rewritten for @goauthentik/web@${releaseVersion}`);
console.log(`prepare-publish: @goauthentik/api pinned to ^${apiVersion}`);
