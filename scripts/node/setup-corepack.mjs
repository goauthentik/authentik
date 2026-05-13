#!/usr/bin/env node

/**
 * @file Downloads the latest corepack tarball from the npm registry.
 */

import * as fs from "node:fs/promises";
import { delimiter, join } from "node:path";
import { parseArgs } from "node:util";

import { ConsoleLogger } from "../../packages/logger-js/lib/node.js";
import { $, parseCWD, reportAndExit } from "./utils/commands.mjs";
import { corepack, pullLatestCorepack, verifyPackageManagerIntegrity } from "./utils/corepack.mjs";
import { resolveRepoRoot } from "./utils/git.mjs";
import { findNPMPackage, loadJSON, npm } from "./utils/node.mjs";

/**
 * @deprecated Remove after Corepack is merged into the monorepo and we can rely on the version specified in package.json.
 */
const FALLBACK_PACKAGE_MANAGER =
    "npm@11.14.1+sha512.6a8a4d67478497a2dbc6815cad72e64c43f33413717e242756047d466241ab39bee61e691683a64658e94496ec5f1a1c05e4a5ec62dcc773280dfd949443a367";
const logger = ConsoleLogger.prefix("setup-corepack");

/**
 * Global npm installs can land outside PATH, especially when npm's prefix is
 * user-scoped. Add that bin directory before checking for or invoking Corepack.
 *
 * @param {string} cwd
 */
async function addNPMGlobalBinToPath(cwd) {
    const npmPrefix = await npm`config get prefix`({ cwd });
    const npmGlobalBin = join(npmPrefix, "bin");
    const path = process.env.PATH || "";

    if (path.split(delimiter).includes(npmGlobalBin)) {
        return;
    }

    process.env.PATH = [npmGlobalBin, path].filter(Boolean).join(delimiter);
}

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

    await addNPMGlobalBinToPath(cwd);

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

    const packageManagerSpec = packageJSONData.packageManager || FALLBACK_PACKAGE_MANAGER;
    const plusIndex = packageManagerSpec.indexOf("+");
    const packageManager =
        plusIndex === -1 ? packageManagerSpec : packageManagerSpec.slice(0, plusIndex);
    const checksum = plusIndex === -1 ? "" : packageManagerSpec.slice(plusIndex + 1);

    if (!checksum) {
        throw new Error(
            `Invalid packageManager field in package.json. Expected format "name@version+checksum". Got "${packageJSONData.packageManager}".`,
        );
    }

    await verifyPackageManagerIntegrity(packageManager, checksum);

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
