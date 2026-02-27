/**
 * Utility functions for working with npm packages and versions.
 *
 * @import { ExecOptions } from "node:child_process"
 */

import * as fs from "node:fs/promises";
import { dirname, join } from "node:path";

import { $ } from "./commands.mjs";

/**
 * Find the nearest directory containing both package.json and package-lock.json,
 * starting from the given directory and walking upward.
 *
 * @param {string} start The directory to start searching from.
 * @returns {Promise<{ packageJSONPath: string, packageLockPath: string }>}
 * @throws {Error} If no co-located package.json and package-lock.json are found.
 */
export async function findNPMPackage(start) {
    let currentDir = start;

    while (currentDir !== dirname(currentDir)) {
        const packageJSONPath = join(currentDir, "package.json");
        const packageLockPath = join(currentDir, "package-lock.json");

        try {
            await Promise.all([fs.access(packageJSONPath), fs.access(packageLockPath)]);
            return {
                packageJSONPath,
                packageLockPath,
            };
        } catch {
            // Continue searching up the directory tree
        }

        currentDir = dirname(currentDir);
    }

    throw new Error(`No co-located package.json and package-lock.json found above ${start}`);
}

/**
 * @typedef {object} PackageJSON
 * @property {string} name
 * @property {string} version
 * @property {Record<string, string>} [dependencies]
 * @property {Record<string, string>} [devDependencies]
 * @property {Record<string, string>} [peerDependencies]
 * @property {Record<string, string>} [optionalDependencies]
 * @property {Record<string, string>} [peerDependenciesMeta]
 * @property {Record<string, string>} [engines]
 * @property {Record<string, string>} [devEngines]
 * @property {string} [packageManager]
 */

/**
 * @param {string} jsonPath
 * @returns {Promise<PackageJSON>}
 */
export function loadJSON(jsonPath) {
    return fs
        .readFile(jsonPath, "utf-8")
        .then(JSON.parse)
        .catch((cause) => {
            throw new Error(`Failed to load JSON file at ${jsonPath}`, { cause });
        });
}

const PackageJSONComparisionFields = /** @type {const} */ ([
    "name",
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
    "peerDependenciesMeta",
]);

/**
 * @typedef {typeof PackageJSONComparisionFields[number]} PackageJSONComparisionField
 */

/**
 * Extracts only the dependency fields from a package.json object for comparison purposes.
 *
 * @param {PackageJSON} data
 * @returns {Pick<PackageJSON, PackageJSONComparisionField>}
 */
export function pluckDependencyFields(data) {
    /**
     * @type {Record<string, unknown>}
     */
    const result = {};

    for (const field of PackageJSONComparisionFields) {
        if (data[field]) {
            result[field] = data[field];
        }
    }

    return /** @type {Pick<PackageJSON, PackageJSONComparisionField>} */ (result);
}

//#region Versioning

/**
 * Compares two semantic version strings (e.g., "14.17.0").
 *
 * @param {string} a The first version string.
 * @param {string} b The second version string.
 * @returns {number}
 */
export function compareVersions(a, b) {
    const pa = a.split(".").map(Number);
    const pb = b.split(".").map(Number);
    for (let i = 0; i < 3; i++) {
        if (pa[i] > pb[i]) return 1;
        if (pa[i] < pb[i]) return -1;
    }
    return 0;
}

/**
 * Runs a Node.js command and returns its stdout output as a string.
 *
 * @param {TemplateStringsArray} strings
 * @param  {...unknown} expressions
 * @returns {(options?: ExecOptions) => Promise<string>}
 */
export const node = $.bind("node");

/**
 * @typedef {object} NPMCommandOptions
 * @property {boolean} [useCorepack] Whether to prefix the command with "corepack " to use Corepack's shims.
 * @returns {Promise<string>}
 */

/**
 * Runs an npm command and returns its stdout output as a string.
 *
 * @param {TemplateStringsArray} strings
 * @param  {...unknown} expressions
 * @returns {(options?: ExecOptions & NPMCommandOptions) => Promise<string>}
 */
export function npm(strings, ...expressions) {
    const subcommand = String.raw(strings, ...expressions);

    return ({ useCorepack, ...options } = {}) => {
        const command = [useCorepack ? "corepack" : "", "npm", subcommand]
            .filter(Boolean)
            .join(" ");

        return $`${command}`(options);
    };
}

/**
 * Parses a version range string, stripping any leading >= and normalizing to three parts.
 * @param {string} range
 * @returns {{ operator: ">=" | "=", version: string }}
 */
export function parseRange(range) {
    const hasGte = range.startsWith(">=");
    const raw = hasGte ? range.slice(2) : range;
    const parts = raw.split(".").map(Number);

    while (parts.length < 3) parts.push(0);

    return {
        operator: hasGte ? ">=" : "=",
        version: parts.join("."),
    };
}

//#endregion
