#!/usr/bin/env node
/**
 * @file Rewrites the web and web-core manifests in place for a public npm publish.
 *
 * Consumers install `@goauthentik/web` as source; the workspace-only bits — the
 * `link:` fallback for the local prettier config, the `link:` reference to the
 * generated `@goauthentik/api` client, and the internal placeholder version —
 * need real values that resolve outside the monorepo.
 *
 * The web leg's `pnpm publish` rewrites `workspace:^` for `@goauthentik/core`
 * against `web/packages/core/package.json`, so that manifest's version must
 * equal the release before the web leg packs — the workflow's core leg is a
 * separate checkout and cannot mutate what the web leg sees. Both manifests
 * are stamped here, and the script is safe to run on either leg.
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
const WEB_MANIFEST_PATH = resolve(WEB_ROOT, "package.json");
const CORE_MANIFEST_PATH = resolve(WEB_ROOT, "packages/core/package.json");

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

async function readManifest(path) {
    return JSON.parse(await readFile(path, "utf8"));
}

async function writeManifest(path, manifest) {
    await writeFile(path, `${JSON.stringify(manifest, null, 4)}\n`);
}

const webManifest = await readManifest(WEB_MANIFEST_PATH);
webManifest.version = releaseVersion;

if (webManifest.dependencies?.["@goauthentik/api"]?.startsWith("link:")) {
    webManifest.dependencies["@goauthentik/api"] = `^${apiVersion}`;
}

if (webManifest.optionalDependencies) {
    for (const [name, spec] of Object.entries(webManifest.optionalDependencies)) {
        if (typeof spec === "string" && (spec.startsWith("link:") || spec.startsWith("file:"))) {
            delete webManifest.optionalDependencies[name];
        }
    }
    if (Object.keys(webManifest.optionalDependencies).length === 0) {
        delete webManifest.optionalDependencies;
    }
}

await writeManifest(WEB_MANIFEST_PATH, webManifest);

const coreManifest = await readManifest(CORE_MANIFEST_PATH);
coreManifest.version = releaseVersion;
await writeManifest(CORE_MANIFEST_PATH, coreManifest);

console.log(`prepare-publish: web/package.json rewritten for @goauthentik/web@${releaseVersion}`);
console.log(`prepare-publish: @goauthentik/api pinned to ^${apiVersion}`);
console.log(`prepare-publish: web/packages/core/package.json stamped to ${releaseVersion}`);
