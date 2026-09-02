#!/usr/bin/env node
/**
 * @file Lints the pnpm version pins that are duplicated across the repo's separate workspaces.
 *
 * Two families of pin are checked: the `catalog:` entries in each `pnpm-workspace.yaml`,
 * and the `packageManager` field plus the pnpm image tags that select pnpm itself.
 *
 * The root, `web/`, and `website/` directories are each their own pnpm workspace
 * (they diverge on `nodeLinker` — the root uses the strict isolated linker for its
 * published packages, while `web` and `website` need `hoisted` for phantom deps).
 * pnpm cannot share a catalog across workspace roots, so each file re-declares the
 * same shared pins.
 *
 * This check fails when a package pinned in more than one workspace
 * drifts out of sync — the manual "keep these in sync" comments already let eslint slip.
 *
 * Usage:
 *   lint-catalogs
 *
 * Exit codes:
 *   0  Every pin agrees
 *   1  A shared package, or pnpm itself, is pinned inconsistently
 */

import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { ConsoleLogger } from "../../packages/logger-js/lib/node.js";
import { reportAndExit } from "./utils/commands.mjs";
import { resolveRepoRoot } from "./utils/git.mjs";

import { parse as parseYAML } from "yaml";

const logger = ConsoleLogger.prefix("lint-catalogs");

/**
 * pnpm workspace roots, each with its own `pnpm-workspace.yaml` and lockfile.
 */
const WORKSPACES: Array<[name: string, filePath: string]> = [
    ["root", "pnpm-workspace.yaml"],
    ["web", "web/pnpm-workspace.yaml"],
    ["website", "website/pnpm-workspace.yaml"],
] as const;

/**
 * The subset of `pnpm-workspace.yaml` we care about: the default `catalog`
 * and any named `catalogs`, both mapping a package name to a version range.
 */
interface PnpmWorkspace {
    catalog?: Record<string, string>;
    catalogs?: Record<string, Record<string, string>>;
}

/**
 * A catalog pin keyed by `<catalog>::<package>` so entries from the default catalog
 * and distinct named catalogs never collide when compared across workspaces.
 */
type Catalog = Map<string, string>;

const DEFAULT_CATALOG = "default";

/**
 * Extracts every catalog pin from a parsed `pnpm-workspace.yaml`,
 * covering both the default `catalog` and any named `catalogs`.
 *
 * @returns A map of `<catalog>::<package>` to version range.
 */
function collectCatalog(source: string): Catalog {
    const workspace = (parseYAML(source) ?? {}) as PnpmWorkspace;
    const catalog: Catalog = new Map();

    const add = (catalogName: string, entries: Record<string, string> | undefined): void => {
        for (const [name, range] of Object.entries(entries ?? {})) {
            catalog.set(`${catalogName}::${name}`, String(range));
        }
    };

    add(DEFAULT_CATALOG, workspace.catalog);

    for (const [catalogName, entries] of Object.entries(workspace.catalogs ?? {})) {
        add(catalogName, entries);
    }

    return catalog;
}

/**
 * Renders a `<catalog>::<package>` key for humans, hiding the redundant default label.
 */
function formatKey(key: string): string {
    const [catalogName, name] = key.split("::", 2);

    return catalogName === DEFAULT_CATALOG ? name : `${name} (catalog: ${catalogName})`;
}

/**
 * Checks that a package pinned in more than one workspace catalog is pinned to the
 * same version everywhere.
 *
 * @returns `true` when a shared package has drifted.
 */
async function lintCatalogPins(repoRoot: string): Promise<boolean> {
    const catalogs = new Map<string, Catalog>();

    for (const [name, filePath] of WORKSPACES) {
        const source = await readFile(join(repoRoot, filePath), "utf-8");
        catalogs.set(name, collectCatalog(source));
    }

    const keys = new Set<string>();

    for (const catalog of catalogs.values()) {
        for (const key of catalog.keys()) {
            keys.add(key);
        }
    }

    let failed = false;

    for (const key of [...keys].sort()) {
        const pins = new Map<string, string>();

        for (const [workspaceName, catalog] of catalogs) {
            const version = catalog.get(key);

            if (version) {
                pins.set(workspaceName, version);
            }
        }

        // Only shared packages can drift; a package pinned in a single workspace is fine.
        if (pins.size < 2) continue;

        const distinct = new Set(pins.values());

        // All workspaces agree on the same version, we're good.
        if (distinct.size === 1) continue;

        const detail = [...pins]
            .map(([workspaceName, version]) => `${workspaceName}=${version}`)
            .join(", ");

        logger.error(`❌ ${formatKey(key)} pinned to differing versions: ${detail}`);
        failed = true;
    }

    if (!failed) {
        logger.info("✅ Catalog pins are in sync across all workspaces.");
    }

    return failed;
}

/**
 * Every manifest that pins pnpm via `packageManager`. They must all agree: an installed
 * pnpm re-execs the version its nearest manifest names, so a stale pin silently runs a
 * different pnpm as a child process.
 */
const PACKAGE_MANAGER_MANIFESTS = [
    "package.json",
    "web/package.json",
    "website/package.json",
    "lifecycle/aws/package.json",
    "packages/client-ts/package.json",
] as const;

/**
 * Dockerfiles that copy the pnpm binary out of the official image. Their tag has to
 * track the `packageManager` version for the same reason.
 */
const PACKAGE_MANAGER_DOCKERFILES = [
    "website/Dockerfile",
    "lifecycle/container/Dockerfile",
] as const;

/**
 * `pnpm@<version>+sha512.<hash>`. The hash is the registry tarball's `dist.integrity`,
 * re-encoded from base64 to hex.
 *
 * Only Corepack ever verified it — pnpm's own version switcher reads the version and
 * ignores the hash. The repo no longer installs pnpm through Corepack, so treat the hash
 * as a checked-in record of exactly which tarball a pin means rather than an enforced
 * gate. It is required here because `pnpm self-update` silently drops it, which is how a
 * bump turns into an unreviewed change of what `packageManager` identifies.
 *
 * To bump, set the new version and re-derive the hash:
 *
 * ```shell
 * node -e 'const v=process.argv[1];fetch(`https://registry.npmjs.org/pnpm/${v}`).then(r=>r.json()).then(d=>{const[alg,b64]=d.dist.integrity.split("-");console.log(`pnpm@${d.version}+${alg}.${Buffer.from(b64,"base64").toString("hex")}`)})' 11.25.0
 * ```
 */
const PACKAGE_MANAGER_PATTERN = /^pnpm@(?<version>[^+\s]+)\+sha512\.(?<hash>[0-9a-f]{128})$/;

/**
 * A pnpm image reference, e.g. `ghcr.io/pnpm/pnpm:11.20.0@sha256:...`.
 */
const PNPM_IMAGE_PATTERN = /ghcr\.io\/pnpm\/pnpm:(?<version>[^@\s]+)/g;

/**
 * Checks that every pnpm pin in the repo names the same version and keeps its
 * Corepack integrity hash.
 *
 * @returns `true` when a pin lost its hash or the pins disagree.
 */
async function lintPackageManagerPins(repoRoot: string): Promise<boolean> {
    let failed = false;

    /** Version to the files declaring it, so a drift report can name the stragglers. */
    const sources = new Map<string, string[]>();
    /** Version to its hash, catching a hand-bumped version left with a stale hash. */
    const hashes = new Map<string, string>();

    const declare = (version: string, filePath: string): void => {
        const declaredIn = sources.get(version);

        if (declaredIn) {
            declaredIn.push(filePath);
        } else {
            sources.set(version, [filePath]);
        }
    };

    for (const filePath of PACKAGE_MANAGER_MANIFESTS) {
        const manifest = JSON.parse(await readFile(join(repoRoot, filePath), "utf-8")) as {
            packageManager?: string;
        };

        if (!manifest.packageManager) {
            logger.error(`❌ ${filePath} has no \`packageManager\` pin.`);
            failed = true;

            continue;
        }

        const groups = PACKAGE_MANAGER_PATTERN.exec(manifest.packageManager)?.groups;

        if (!groups) {
            logger.error(
                `❌ ${filePath} pins \`${manifest.packageManager}\`, which is not of the form ` +
                    "`pnpm@<version>+sha512.<hash>`. `pnpm self-update` strips the hash — " +
                    "re-derive it with the snippet documented on `PACKAGE_MANAGER_PATTERN` " +
                    "in this file.",
            );

            failed = true;

            continue;
        }

        const { version, hash } = groups;
        const knownHash = hashes.get(version);

        if (!knownHash) {
            hashes.set(version, hash);
        } else if (knownHash !== hash) {
            logger.error(
                `❌ ${filePath} pins pnpm ${version} with a hash the other manifests disagree with.`,
            );

            failed = true;
        }

        declare(version, filePath);
    }

    for (const filePath of PACKAGE_MANAGER_DOCKERFILES) {
        const source = await readFile(join(repoRoot, filePath), "utf-8");

        for (const match of source.matchAll(PNPM_IMAGE_PATTERN)) {
            const version = match.groups?.version;

            if (version) {
                declare(version, filePath);
            }
        }
    }

    if (sources.size > 1) {
        const detail = [...sources]
            .sort(([left], [right]) => left.localeCompare(right))
            .map(([version, declaredIn]) => `${version} (${declaredIn.join(", ")})`)
            .join("; ");

        logger.error(`❌ pnpm is pinned to differing versions: ${detail}`);
        failed = true;
    }

    if (!failed) {
        logger.info(`✅ pnpm ${[...sources.keys()][0]} is pinned consistently, hash intact.`);
    }

    return failed;
}

async function main(): Promise<void> {
    const repoRoot = await resolveRepoRoot();

    // Both checks run so a single invocation reports every drift, not just the first.
    const catalogsDrifted = await lintCatalogPins(repoRoot);
    const packageManagerDrifted = await lintPackageManagerPins(repoRoot);

    if (catalogsDrifted || packageManagerDrifted) {
        throw new Error("pnpm pins are out of sync. Reconcile them.");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => reportAndExit(error, logger));
