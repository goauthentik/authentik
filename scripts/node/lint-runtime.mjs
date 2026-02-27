#!/usr/bin/env node
/**
 * @file Lints the installed Node.js and npm versions against the requirements specified in package.json.
 *
 * Usage:
 *   lint-node [options] [directory]
 *
 * Exit codes:
 *   0  Versions are in sync
 *   1  Version mismatch detected
 */

import * as assert from "node:assert/strict";
import { parseArgs } from "node:util";

import { ConsoleLogger } from "../../packages/logger-js/lib/node.js";
import { CommandError, parseCWD, reportAndExit } from "./utils/commands.mjs";
import { corepack } from "./utils/corepack.mjs";
import { resolveRepoRoot } from "./utils/git.mjs";
import { compareVersions, findNPMPackage, loadJSON, node, npm, parseRange } from "./utils/node.mjs";

const logger = ConsoleLogger.prefix("lint-runtime");

/**
 * @param {string} start
 */
async function readRequirements(start) {
    const { packageJSONPath } = await findNPMPackage(start);

    logger.info(`Checking versions in ${packageJSONPath}`);

    const packageJSONData = await loadJSON(packageJSONPath);

    const nodeVersion = await node`--version`().then((output) => output.replace(/^v/, ""));

    const requiredNpmVersion = packageJSONData.engines?.npm;
    const requiredNodeVersion = packageJSONData.engines?.node;

    return { nodeVersion, requiredNpmVersion, requiredNodeVersion };
}

async function main() {
    const parsedArgs = parseArgs({
        allowPositionals: true,
    });

    const cwd = parseCWD(parsedArgs.positionals);
    const repoRoot = await resolveRepoRoot(cwd).catch(() => null);

    logger.info(`cwd ${cwd}`);
    logger.info(`repository ${repoRoot || "not found"}`);

    const corepackVersion = await corepack`--version`().catch(() => null);
    const useCorepack = !!corepackVersion;
    logger.info(`corepack ${corepackVersion || "disabled"}`);

    const npmVersion = await npm`--version`({ cwd, useCorepack })
        .then((version) => {
            logger.info(`npm${corepackVersion ? " (via Corepack)" : ""} ${version}`);

            return version;
        })
        .catch((error) => {
            if (error instanceof CommandError && corepackVersion) {
                logger.warn(`Failed to read npm version via Corepack ${error.message}`);

                logger.info(`Attempting to read npm version directly without Corepack...`);
                // Corepack might be misconfigured or outdated.
                // Attempting a second read without Corepack can help us distinguish
                // between a general npm issue and a Corepack-specific one.
                return npm`--version`({ cwd }).then((version) => {
                    logger.info(`npm (direct) ${version}`);

                    return version;
                });
            }

            throw error;
        });

    const { nodeVersion, requiredNpmVersion, requiredNodeVersion } = await readRequirements(cwd);

    logger.info(`node ${nodeVersion}`);

    if (requiredNpmVersion) {
        logger.info(`package.json npm ${requiredNpmVersion}`);

        const { operator, version: required } = parseRange(requiredNpmVersion);
        const result = compareVersions(npmVersion, required);

        assert.ok(
            operator === ">=" ? result >= 0 : result === 0,
            `npm version ${npmVersion} does not satisfy required version ${requiredNpmVersion}`,
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
        logger.info("✅ Node.js and npm versions are in sync.");
    })
    .catch((error) => reportAndExit(error, logger));
