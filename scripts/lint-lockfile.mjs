#!/usr/bin/env node
/**
 * @file Lints the package-lock.json file to ensure it is in sync with package.json.
 *
 * Usage:
 *   lint-lockfile [options] [directory]
 *
 * Options:
 *   --warn    Report issues as warnings instead of failing. The lockfile is
 *             still regenerated on disk, but the process exits 0.
 *
 * Exit codes:
 *   0  Lockfile is in sync (or --warn was passed)
 *   1  Unexpected error
 *   2  Lockfile drift detected
 */

import * as assert from "node:assert/strict";
import { exec } from "node:child_process";
import * as fs from "node:fs/promises";
import { findPackageJSON } from "node:module";
import * as path from "node:path";
import { isDeepStrictEqual, promisify } from "node:util";

//#region Utilities

const execAsync = promisify(exec);

const prefix = "(lint:lockfile)";
const logger = {
    info: console.info.bind(console, "INFO", prefix),
    error: console.error.bind(console, "ERROR", prefix),
    warn: console.warn.bind(console, "WARN", prefix),
};

/**
 * Find the nearest directory containing both package.json and package-lock.json,
 * starting from the given directory and walking upward.
 *
 * @param {string} start The directory to start searching from.
 * @returns {Promise<string>} The path to the package-lock.json file.
 * @throws {Error} If no co-located package.json and package-lock.json are found.
 */
async function findNearestLockfile(start) {
    let currentDir = start;

    while (currentDir !== path.dirname(currentDir)) {
        const packageJSONPath = path.join(currentDir, "package.json");
        const lockfilePath = path.join(currentDir, "package-lock.json");

        try {
            await Promise.all([fs.access(packageJSONPath), fs.access(lockfilePath)]);
            return lockfilePath;
        } catch {
            // Continue searching up the directory tree
        }

        currentDir = path.dirname(currentDir);
    }

    throw new Error(`No co-located package.json and package-lock.json found above ${start}`);
}

/**
 * @param {string} jsonPath
 * @returns {Promise<Record<string, unknown>>}
 */
function loadJSON(jsonPath) {
    return fs
        .readFile(jsonPath, "utf-8")
        .then(JSON.parse)
        .catch((cause) => {
            throw new Error(`Failed to load JSON file at ${jsonPath}`, { cause });
        });
}

/**
 * Checks whether the given file has uncommitted changes in git.
 *
 * @param {string} filePath
 * @returns {Promise<{ clean: boolean, available: boolean }>}
 */
async function gitStatus(filePath) {
    try {
        const { stdout } = await execAsync(`git status --porcelain ${filePath}`);
        return { clean: !stdout.trim(), available: true };
    } catch {
        return { clean: false, available: false };
    }
}

/**
 * @typedef {{
 *   warnOnly: boolean;
 *   cwd: string;
 * }} Options
 */

/**
 * @param {string[]} argv
 * @returns {Options}
 */
function parseArgs(argv) {
    const args = argv.slice(2);
    let warnOnly = false;
    /** @type {string[]} */
    const positional = [];

    for (const arg of args) {
        if (arg === "--warn") {
            warnOnly = true;
        } else if (arg.startsWith("-")) {
            logger.error(`Unknown option: ${arg}`);
            process.exit(1);
        } else {
            positional.push(arg);
        }
    }

    // `INIT_CWD` is present only if the script is run via npm.
    const initCWD = process.env.INIT_CWD || process.cwd();

    const cwd = (positional.length ? path.resolve(initCWD, positional[0]) : initCWD) + path.sep;

    return { warnOnly, cwd };
}

//#endregion

/**
 * Exit code when lockfile drift is detected (distinct from general errors)
 */
const EXIT_DRIFT = 2;

/**
 * @param {Options} options
 * @returns {Promise<string[]>} The list of issues detected.
 */
async function run({ warnOnly, cwd }) {
    /** @type {string[]} */
    const issues = [];

    /**
     * Records an issue. In strict mode, throws immediately.
     * In warn mode, collects the message for later reporting.
     *
     * @param {boolean} ok
     * @param {string} message
     */
    const check = (ok, message) => {
        if (ok) return;

        if (warnOnly) {
            issues.push(message);
            return;
        }

        assert.fail(message);
    };

    logger.info(`Checking lockfile integrity in: ${cwd}`);

    // MARK: Locate files

    const resolvedPath = import.meta.resolve(cwd);
    const packageJSONPath = findPackageJSON(resolvedPath);

    assert.ok(
        packageJSONPath,
        "Could not find package.json in the current directory or any parent directories",
    );

    const packageDir = path.dirname(packageJSONPath);
    const lockfilePath = await findNearestLockfile(packageDir);
    const lockfileDir = path.dirname(lockfilePath);
    const isWorkspace = lockfileDir !== packageDir;

    const before = {
        lockfile: await loadJSON(lockfilePath),
        package: await loadJSON(packageJSONPath),
    };

    logger.info(`package.json: ${packageJSONPath} (${before.package.name})`);
    logger.info(`package-lock.json: ${lockfilePath}${isWorkspace ? " (workspace root)" : ""}`);

    // MARK: Uncommitted changes

    const packageStatus = await gitStatus(packageJSONPath);
    const lockfileStatus = await gitStatus(lockfilePath);

    if (!packageStatus.available || !lockfileStatus.available) {
        logger.warn("Git is not available; skipping uncommitted change detection.");
    } else {
        check(packageStatus.clean, `package.json has uncommitted changes: ${packageJSONPath}`);

        check(lockfileStatus.clean, `package-lock.json has uncommitted changes: ${lockfilePath}`);
    }

    // MARK: Regenerate

    logger.info("Running npm install --package-lock-only...");

    await execAsync("npm install --package-lock-only", {
        cwd: lockfileDir,
    }).catch((cause) => {
        throw new Error("npm install --package-lock-only failed", { cause });
    });

    logger.info("npm install complete.");

    const after = {
        lockfile: await loadJSON(lockfilePath),
        package: await loadJSON(packageJSONPath),
    };

    // MARK: Compare

    assert.ok(
        isDeepStrictEqual(before.package, after.package),
        `package.json was unexpectedly modified during lockfile check: ${packageJSONPath}`,
    );

    check(
        isDeepStrictEqual(before.lockfile, after.lockfile),
        `package-lock.json is out of sync with package.json`,
    );

    return issues;
}

const options = parseArgs(process.argv);

run(options)
    .then((issues) => {
        if (issues.length) {
            logger.warn(`⚠️  ${issues.length} issue(s) detected:`);

            for (const issue of issues) {
                logger.warn(`  - ${issue}`);
            }

            if (options.warnOnly) {
                logger.warn(
                    "The lockfile on disk has been regenerated. Review and commit the changes.",
                );
                process.exit(EXIT_DRIFT);
            }
        } else {
            logger.info("✅ Lockfile is in sync.");
        }
    })
    .catch((error) => {
        const message = error instanceof Error ? error.message : String(error);
        const cause = error instanceof Error && error.cause instanceof Error ? error.cause : null;

        logger.error(`❌ ${message}`);

        if (cause) {
            logger.error("Caused by:", cause);
        }

        process.exit(1);
    });
