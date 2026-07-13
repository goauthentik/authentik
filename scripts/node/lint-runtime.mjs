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

import { ConsoleLogger } from "../../packages/logger-js/lib/node.js";
import { parseCWD, reportAndExit } from "./utils/commands.mjs";
import { resolveRepoRoot } from "./utils/git.mjs";
import { compareVersions, findNPMPackage, loadJSON, node, pnpm, parseRange } from "./utils/node.mjs";

const logger = ConsoleLogger.prefix("lint-runtime");

/**
 * @param {string} start
 */
async function readRequirements(start) {
    const { packageJSONPath } = await findNPMPackage(start);

    logger.info(`Checking versions in ${packageJSONPath}`);

    const packageJSONData = await loadJSON(packageJSONPath);

    const nodeVersion = await node`--version`().then((output) => output.replace(/^v/, ""));

    const requiredPnpmVersion = packageJSONData.engines?.pnpm;
    const requiredNodeVersion = packageJSONData.engines?.node;

    return { nodeVersion, requiredPnpmVersion, requiredNodeVersion };
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

    const { nodeVersion, requiredPnpmVersion, requiredNodeVersion } = await readRequirements(cwd);

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
}

main()
    .then(() => {
        logger.info("✅ Node.js and pnpm versions are in sync.");
        process.exit(0);
    })
    .catch((error) => reportAndExit(error, logger));
