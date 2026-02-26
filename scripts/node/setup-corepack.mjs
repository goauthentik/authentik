#!/usr/bin/env node

/**
 * @file Downloads the latest corepack tarball from the npm registry.
 */

import * as fs from "node:fs/promises";
import { parseArgs } from "node:util";

import { ConsoleLogger } from "../../packages/logger-js/lib/node.js";
import { $, parseCWD, reportAndExit } from "./utils/commands.mjs";
import { corepack, pullLatestCorepack } from "./utils/corepack.mjs";
import { resolveRepoRoot } from "./utils/git.mjs";
import { findNPMPackage, loadJSON, npm } from "./utils/node.mjs";

const FALLBACK_NPM_VERSION = "11.11.0";
const logger = ConsoleLogger.prefix("setup-corepack");

async function main() {
    const parsedArgs = parseArgs({
        options: {
            force: {
                type: "boolean",
                default: false,
                description: "Force re-download of corepack even if a version is already installed",
            },
        },
        allowPositionals: true,
    });

    const cwdArg = parseCWD(parsedArgs.positionals);

    const repoRoot = await resolveRepoRoot(cwdArg).catch(() => null);
    const cwd = repoRoot || cwdArg;

    const npmVersion = await npm`--version`({ cwd });

    logger.info(`npm ${npmVersion}`);

    const corepackVersion = await corepack`--version`({ cwd }).catch(() => null);

    logger.info(`corepack ${corepackVersion || "not found"}`);

    if (corepackVersion && !parsedArgs.values.force) {
        logger.info("Corepack is already installed, skipping download (use --force to override)");
        return;
    }

    await pullLatestCorepack(cwd);

    await npm`install --force -g corepack@latest`({ cwd });
    logger.info("Corepack installed successfully");

    const { packageJSONPath } = await findNPMPackage(cwd);

    logger.info(`Checking versions in ${packageJSONPath}`);

    const packageJSONData = await loadJSON(packageJSONPath);

    const packageManager = packageJSONData.packageManager || `npm@${FALLBACK_NPM_VERSION}`;

    await $`corepack install -g ${packageManager}`({ cwd });

    logger.info(`Setting up Corepack to use ${packageManager}...`);

    const writablePackageJSON = await fs.access(packageJSONPath, fs.constants.W_OK).then(
        () => true,
        () => false,
    );

    /**
     * @type {string}
     */
    let subcommand;

    if (!writablePackageJSON) {
        if (!packageJSONData.packageManager) {
            throw new Error(
                `package.json is not writable and does not specify a packageManager field. Was the package.json file mounted via Docker?`,
            );
        }

        subcommand = "install -g";
    } else {
        logger.info("package.json is writable");
        subcommand = "use";
    }

    await $`corepack ${subcommand} ${packageManager}`({ cwd });

    logger.info("Corepack installed npm successfully");
}

main().catch((error) => reportAndExit(error, logger));
