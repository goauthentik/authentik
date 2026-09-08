/**
 * Utility functions for working with npm packages and versions.
 *
 * @import { ExecOptions } from "node:child_process"
 */

import * as fs from "node:fs/promises";
import { dirname, join } from "node:path";

import { $ } from "./commands.mjs";

/**
 * Find the nearest directory containing both package.json and pnpm-lock.yaml,
 * starting from the given directory and walking upward.
 *
 * @param {string} start The directory to start searching from.
 * @returns {Promise<{ packageJSONPath: string, packageLockPath: string }>}
 * @throws {Error} If no co-located package.json and pnpm-lock.yaml are found.
 */
export async function findNPMPackage(start) {
    let currentDir = start;

    while (currentDir !== dirname(currentDir)) {
        const packageJSONPath = join(currentDir, "package.json");
        const packageLockPath = join(currentDir, "pnpm-lock.yaml");

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

    throw new Error(`No co-located package.json and pnpm-lock.yaml found above ${start}`);
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

const PackageJSONComparisonFields = /** @type {const} */ ([
    "name",
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
    "peerDependenciesMeta",
]);

/**
 * @typedef {typeof PackageJSONComparisonFields[number]} PackageJSONComparisonField
 */

/**
 * Extracts only the dependency fields from a package.json object for comparison purposes.
 *
 * @param {PackageJSON} data
 * @returns {Pick<PackageJSON, PackageJSONComparisonField>}
 */
export function pluckDependencyFields(data) {
    /**
     * @type {Record<string, unknown>}
     */
    const result = {};

    for (const field of PackageJSONComparisonFields) {
        if (data[field]) {
            result[field] = data[field];
        }
    }

    return /** @type {Pick<PackageJSON, PackageJSONComparisonField>} */ (result);
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
 * Runs a pnpm command and returns its stdout output as a string.
 *
 * @param {TemplateStringsArray} strings
 * @param  {...unknown} expressions
 * @returns {(options?: ExecOptions) => Promise<string>}
 */
export const pnpm = $.bind("pnpm");

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

//#region Package manager

/**
 * The npm registry used to resolve the integrity hash of a `packageManager` pin.
 */
const NPM_REGISTRY_ORIGIN = process.env.npm_config_registry || "https://registry.npmjs.org";

/**
 * How long to wait on the registry before giving up on the integrity check.
 */
const REGISTRY_TIMEOUT_MS = 10 * 1000;

/**
 * @typedef {object} PackageManagerSpec
 * @property {string} name The package manager's package name, e.g. `pnpm`.
 * @property {string} version The exact pinned version, e.g. `12.4.0`.
 * @property {string | null} hash The `sha512.<hex>` suffix, if the pin carries one.
 */

/**
 * Parses a `packageManager` field, i.e. `pnpm@12.4.0+sha512.37536c26...`
 *
 * @param {string} spec
 * @returns {PackageManagerSpec}
 * @throws {Error} If the field isn't a `<name>@<version>` pin.
 */
export function parsePackageManager(spec) {
    const match = /^(?<name>@?[^@]+)@(?<version>[^+]+)(?:\+(?<hash>.+))?$/.exec(spec.trim());

    if (!match?.groups) {
        throw new Error(`Malformed packageManager field: ${spec}`);
    }

    const { name, version, hash } = match.groups;

    return { name, version, hash: hash || null };
}

/**
 * Serializes a {@linkcode PackageManagerSpec} back into a `packageManager` field.
 *
 * @param {PackageManagerSpec} spec
 * @returns {string}
 */
export function formatPackageManager({ name, version, hash }) {
    return `${name}@${version}` + (hash ? `+${hash}` : "");
}

/**
 * Resolves the expected `sha512.<hex>` suffix for a `packageManager` pin.
 *
 * The npm registry publishes the tarball's integrity as base64 (`sha512-<base64>`),
 * while `packageManager` spells the same digest as hex.
 *
 * @param {string} name The package manager's package name, e.g. `pnpm`.
 * @param {string} version The exact version to look up.
 * @returns {Promise<string>}
 * @throws {Error} If the registry can't be reached, or the version isn't published.
 */
export async function resolvePackageManagerHash(name, version) {
    const packageURL = `${NPM_REGISTRY_ORIGIN.replace(/\/$/, "")}/${encodeURIComponent(name)}/${encodeURIComponent(version)}`;

    const response = await fetch(packageURL, {
        headers: { accept: "application/json" },
        signal: AbortSignal.timeout(REGISTRY_TIMEOUT_MS),
    }).catch((cause) => {
        throw new Error(`Failed to reach the npm registry at ${packageURL}`, { cause });
    });

    if (!response.ok) {
        throw new Error(
            `Registry returned ${response.status} ${response.statusText} for ${packageURL}`,
        );
    }

    /**
     * @type {{ dist?: { integrity?: string } }}
     */
    const manifest = await response.json();
    const integrity = manifest.dist?.integrity;

    if (!integrity) {
        throw new Error(`Registry manifest for ${name}@${version} has no dist.integrity`);
    }

    const [algorithm, encoded] = integrity.split("-");

    return `${algorithm}.${Buffer.from(encoded, "base64").toString("hex")}`;
}

//#endregion
