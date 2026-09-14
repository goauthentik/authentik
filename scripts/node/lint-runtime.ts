#!/usr/bin/env node
/**
 * @file Lints the installed Node.js and pnpm versions against the requirements specified in package.json.
 *
 * Usage:
 *   lint-runtime [options] [directory]
 *
 * Exit codes:
 *   0  Versions are in sync
 *   1  Version mismatch detected
 */

import * as assert from "node:assert/strict";
import { parseArgs } from "node:util";

import { parseCWD, reportAndExit } from "./utils/commands.ts";
import { resolveRepoRoot } from "./utils/git.ts";
import type { PackageJSON } from "./utils/node.ts";
import {
    compareVersions,
    findNPMPackage,
    formatPackageManager,
    loadJSON,
    node,
    parsePackageManager,
    parseRange,
    pnpm,
    resolvePackageManagerHash,
} from "./utils/node.ts";

import { ConsoleLogger } from "#logger";

const logger = ConsoleLogger.prefix("lint-runtime");

async function readRequirements(start: string) {
    const { packageJSONPath } = await findNPMPackage(start);

    logger.info(`Checking versions in ${packageJSONPath}`);

    const packageJSONData = await loadJSON<PackageJSON>(packageJSONPath);

    const nodeVersion = await node`--version`().then((output) => output.replace(/^v/, ""));

    const requiredPnpmVersion = packageJSONData.engines?.pnpm;
    const requiredNodeVersion = packageJSONData.engines?.node;
    const packageManager = packageJSONData.packageManager;

    return { nodeVersion, requiredPnpmVersion, requiredNodeVersion, packageManager };
}

async function main() {
    const parsedArgs = parseArgs({
        allowPositionals: true,
    });

    const cwd = parseCWD(parsedArgs.positionals);
    const repoRoot = await resolveRepoRoot(cwd).catch(() => null);

    logger.info(`cwd ${cwd}`);
    logger.info(`repository ${repoRoot || "not found"}`);

    const pnpmVersion = await pnpm`--version`({ cwd }).catch((error) => {
        logger.warn(`Failed to read pnpm version: ${error.message}`);
        return null;
    });

    if (pnpmVersion) {
        logger.info(`pnpm ${pnpmVersion}`);
    }

    const { nodeVersion, requiredPnpmVersion, requiredNodeVersion, packageManager } =
        await readRequirements(cwd);

    logger.info(`node ${nodeVersion}`);

    if (requiredPnpmVersion && pnpmVersion) {
        logger.info(`package.json pnpm ${requiredPnpmVersion}`);

        const { operator, version: required } = parseRange(requiredPnpmVersion);
        const result = compareVersions(pnpmVersion, required);

        assert.ok(
            operator === ">=" ? result >= 0 : result === 0,
            `pnpm version ${pnpmVersion} does not satisfy required version ${requiredPnpmVersion}`,
        );
    }

    if (requiredNodeVersion) {
        logger.info(`package.json node ${requiredNodeVersion}`);

        const { operator, version: required } = parseRange(requiredNodeVersion);
        const result = compareVersions(nodeVersion, required);

        assert.ok(
            operator === ">=" ? result >= 0 : result === 0,
            `Node.js version ${nodeVersion} does not satisfy required version ${requiredNodeVersion}`,
        );
    }

    if (packageManager) {
        await lintPackageManager(packageManager, requiredPnpmVersion);
    }
}

/**
 * Checks that the `packageManager` pin names a version allowed by `engines`, and that its
 * integrity suffix matches the tarball the registry actually publishes for that version.
 *
 * Corepack used to verify this suffix on our behalf. Now that it's deprecated, nothing else
 * reads it — so a stale hash would sit in package.json unnoticed until someone trusted it.
 *
 * @param packageManager The raw `packageManager` field.
 * @param requiredPnpmVersion  The `engines.pnpm` range, when present.
 */
async function lintPackageManager(packageManager: string, requiredPnpmVersion?: string) {
    logger.info(`package.json packageManager ${packageManager}`);

    const spec = parsePackageManager(packageManager);

    if (requiredPnpmVersion && spec.name === "pnpm") {
        const { operator, version: required } = parseRange(requiredPnpmVersion);
        const result = compareVersions(spec.version, required);

        assert.ok(
            operator === ">=" ? result >= 0 : result === 0,
            `packageManager pins pnpm ${spec.version}, which does not satisfy engines.pnpm ${requiredPnpmVersion}`,
        );
    }

    if (!spec.hash) {
        logger.warn("packageManager has no integrity suffix; skipping hash check.");
        return;
    }

    const expectedHash = await resolvePackageManagerHash(spec.name, spec.version).catch((error) => {
        logger.warn(`Skipping integrity check: ${error.message}`);
        return null;
    });

    if (!expectedHash) return;

    assert.ok(
        spec.hash === expectedHash,
        `packageManager integrity does not match the published ${spec.name}@${spec.version} tarball.\n` +
            `Copy this into package.json:\n\n` +
            `    "packageManager": "${formatPackageManager({ ...spec, hash: expectedHash })}"\n`,
    );
}

main()
    .then(() => {
        logger.info("✅ Node.js and pnpm versions are in sync.");
        process.exit(0);
    })
    .catch((error) => reportAndExit(error, logger));
