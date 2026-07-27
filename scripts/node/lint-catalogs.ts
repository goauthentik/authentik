#!/usr/bin/env node
/**
 * @file Lints the pnpm `catalog:` version pins across the repo's separate workspaces.
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
 *   0  Catalogs agree
 *   1  A shared package is pinned to differing versions
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

async function main(): Promise<void> {
    const repoRoot = await resolveRepoRoot();

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

    if (failed) {
        throw new Error("Catalog pins are out of sync across workspaces. Reconcile them.");
    }

    logger.info("✅ Catalog pins are in sync across all workspaces.");
}

main()
    .then(() => process.exit(0))
    .catch((error) => reportAndExit(error, logger));
