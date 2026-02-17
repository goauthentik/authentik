#!/usr/bin/env node
/**
 * @file Lints the package-lock.json file to ensure it is in sync with package.json.
 */

import * as assert from "node:assert/strict";
import { exec } from "node:child_process";
import * as fs from "node:fs/promises";
import { findPackageJSON } from "node:module";
import * as path from "node:path";
import { isDeepStrictEqual, promisify } from "node:util";

const execAsync = promisify(exec);

const prefix = "(lint)";
const logger = {
    info: console.info.bind(console, "INFO", prefix),
    error: console.error.bind(console, "ERROR", prefix),
    warn: console.warn.bind(console, "WARN", prefix),
};

/**
 * Find the nearest package.json and package-lock.json files starting from the given directory.
 *
 * @param {string} start The directory to start searching from.
 * @returns {Promise<string>}
 * @throws {Error} If no package.json or package-lock.json file is found.
 */
async function findNearestPackageJSONLockfile(start) {
    let currentDir = start;

    while (currentDir !== path.dirname(currentDir)) {
        const packageJSONPath = path.join(currentDir, "package.json");
        const lockfileJSONPath = path.join(currentDir, "package-lock.json");

        try {
            await Promise.all([fs.access(packageJSONPath), fs.access(lockfileJSONPath)]);

            return lockfileJSONPath;
        } catch {
            // Ignore and continue searching up the directory tree
        }

        currentDir = path.dirname(currentDir);
    }

    throw new Error(
        "No package.json or package-lock.json file found in the current directory or any parent directories.",
    );
}

/**
 * @param {string} jsonPath
 * @returns {Promise<Record<string, unknown>>}
 */
function load(jsonPath) {
    return fs
        .readFile(jsonPath, "utf-8")
        .then(JSON.parse)
        .catch((cause) => {
            throw new Error(`Failed to load JSON file at ${jsonPath}`, { cause });
        });
}

/**
 * If Git is available, checks if the given file has uncommitted changes. If so, returns true. Otherwise, returns false.
 *
 * @param {string} filePath
 * @returns {Promise<boolean>}
 */
async function checkIfClean(filePath) {
    try {
        const { stdout } = await execAsync(`git status --porcelain ${filePath}`);

        return !stdout.trim();
    } catch (error) {
        logger.warn("Failed to check if file is staged. Is Git available?", { error });

        return true;
    }
}

const FIX_ARG = "--fix";

/**
 *
 * @returns {Promise<string[]>} The list of issues detected.
 */
async function run() {
    let args = process.argv.slice(2);
    let strictAssertions = true;

    if (args.includes(FIX_ARG)) {
        strictAssertions = false;
        args = args.filter((arg) => arg !== FIX_ARG);
        logger.info("Issues will be reported but not treated as errors.");
    }

    /**
     * @type {string[]}
     */
    let issues = [];

    /**
     * @param {boolean} predicate
     * @param {string} message
     * @returns {void}
     */
    const assertIfStrict = (predicate, message) => {
        if (predicate) return;

        if (!strictAssertions) {
            issues.push(message);
            return;
        }

        return assert.fail(message);
    };

    let cwd;

    if (args.length >= 1) {
        cwd = path.resolve(args[0]) + path.sep;
    } else {
        cwd = process.cwd() + path.sep;
    }

    logger.info(`Starting lockfile linting in directory: ${cwd}`);

    logger.info("Finding nearest package.json and package-lock.json...");

    const resolvedPath = import.meta.resolve(cwd);
    const packageJSONPath = findPackageJSON(resolvedPath);

    assert.ok(
        packageJSONPath,
        "Could not find package.json in the current directory or any parent directories",
    );

    const packageDir = path.dirname(packageJSONPath);

    logger.info("Finding nearest package-lock.json...");

    const lockfileJSONPath = await findNearestPackageJSONLockfile(packageDir);
    const lockfileDir = path.dirname(lockfileJSONPath);
    const workspace = lockfileDir !== packageDir;

    const initial = {
        lockfile: await load(lockfileJSONPath),
        package: await load(packageJSONPath),
    };

    logger.info(`(${initial.package.name}) package.json`, packageJSONPath);

    logger.info(
        `(${initial.lockfile.name}) ${workspace ? "(workspace) " : ""}package-lock.json`,
        lockfileJSONPath,
    );

    assertIfStrict(
        await checkIfClean(packageJSONPath),
        `package.json (${packageJSONPath}) has uncommitted changes`,
    );

    assertIfStrict(
        await checkIfClean(lockfileJSONPath),
        `Lockfile (${lockfileJSONPath}) has uncommitted changes`,
    );

    logger.info(`Running npm install for ${initial.lockfile.name}...`);

    await execAsync("npm install --package-lock-only", {
        cwd: lockfileDir,
    }).catch((cause) => {
        throw new Error("Failed to run `npm install`", { cause });
    });

    logger.info(`Finished npm install for ${initial.lockfile.name}`);

    const updated = {
        lockfile: await load(lockfileJSONPath),
        package: await load(packageJSONPath),
    };

    assert.ok(
        isDeepStrictEqual(initial.package, updated.package),
        `package.json (${packageJSONPath}) was unexpectedly modified during lockfile check`,
    );

    assertIfStrict(
        isDeepStrictEqual(initial.lockfile, updated.lockfile),
        `Lockfile (${lockfileJSONPath}) is not in sync with package.json`,
    );

    return issues;
}

run()
    .then((issues) => {
        if (issues) {
            logger.warn(
                `⚠️ Completed with ${issues.length} issue(s). Please review the warnings and commit any necessary changes.`,
            );

            for (const issue of issues) {
                logger.warn(`\t- ${issue}`);
            }
        } else {
            logger.info("✅ Lockfile is synchronized!");
        }
    })
    .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        const supplemental =
            error instanceof Error && error.cause instanceof Error ? error.cause : null;

        logger.error(`❌ ${message}`);

        if (supplemental) {
            logger.error("Caused by:", supplemental);
        }

        process.exit(1);
    });
