/**
 * Utility functions for working with npm packages and versions.
 */

import * as fs from "node:fs/promises";
import { dirname, join } from "node:path";

import { $ } from "./commands.ts";

/**
 * Find the nearest directory containing both package.json and pnpm-lock.yaml,
 * starting from the given directory and walking upward.
 *
 * @param start The directory to start searching from.
 * @throws {Error} If no co-located package.json and pnpm-lock.yaml are found.
 */
export async function findNPMPackage(
    start: string,
): Promise<{ packageJSONPath: string; packageLockPath: string }> {
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

export interface PackageJSON {
    name: string;
    version: string;
    dependencies?: Record<string, string>;
    devDependencies?: Record<string, string>;
    peerDependencies?: Record<string, string>;
    optionalDependencies?: Record<string, string>;
    peerDependenciesMeta?: Record<string, { optional?: boolean }>;
    engines?: Record<string, string>;
    devEngines?: Record<string, string>;
    packageManager?: string;
}

export function loadJSON<T = unknown>(jsonPath: string): Promise<T> {
    return fs
        .readFile(jsonPath, "utf-8")
        .then(JSON.parse)
        .catch((cause) => {
            throw new Error(`Failed to load JSON file at ${jsonPath}`, { cause });
        });
}

const PackageJSONComparisonFields = [
    "name",
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
    "peerDependenciesMeta",
] as const satisfies ReadonlyArray<keyof PackageJSON>;

export type PackageJSONComparisonField = (typeof PackageJSONComparisonFields)[number];

/**
 * Extracts only the dependency fields from a package.json object for comparison purposes.
 */
export function pluckDependencyFields(
    data: PackageJSON,
): Pick<PackageJSON, PackageJSONComparisonField> {
    const result: Record<string, unknown> = {};

    for (const field of PackageJSONComparisonFields) {
        if (data[field]) {
            result[field] = data[field];
        }
    }

    return result as Pick<PackageJSON, PackageJSONComparisonField>;
}

//#region Versioning

/**
 * Compares two semantic version strings (e.g., "14.17.0").
 *
 * A missing part counts as zero, so "24" and "24.0.0" compare equal.
 *
 * @param a The first version string.
 * @param b The second version string.
 */
export function compareVersions(a: string, b: string): number {
    const pa = a.split(".").map(Number);
    const pb = b.split(".").map(Number);

    for (let i = 0; i < 3; i++) {
        const left = pa[i] ?? 0;
        const right = pb[i] ?? 0;

        if (left > right) return 1;
        if (left < right) return -1;
    }

    return 0;
}

/**
 * Runs a Node.js command and returns its stdout output as a string.
 */
export const node = $.bind("node");

/**
 * Runs a pnpm command and returns its stdout output as a string.
 */
export const pnpm = $.bind("pnpm");

/**
 * Parses a version range string, stripping any leading >= and normalizing to three parts.
 */
export function parseRange(range: string): { operator: ">=" | "="; version: string } {
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

interface PackageManagerSpec {
    /**
     * The package manager's package name, e.g. `pnpm`.
     */
    name: string;

    /**
     * The exact pinned version, e.g. `12.4.0`.
     */
    version: string;

    /**
     * The `sha512.<hex>` suffix, if the pin carries one.
     */
    hash: string | null;
}

const PACKAGE_MANAGER_PATTERN = /^(?<name>@?[^@]+)@(?<version>[^+]+)(?:\+(?<hash>.+))?$/;

/**
 * The named groups of {@linkcode PACKAGE_MANAGER_PATTERN}. Only `hash` is optional
 * in the pattern, so a match always carries the other two.
 */
interface PackageManagerGroups {
    name: string;
    version: string;
    hash?: string;
}

/**
 * Parses a `packageManager` field, i.e. `pnpm@12.4.0+sha512.37536c26...`
 *
 * @throws {Error} If the field isn't a `<name>@<version>` pin.
 */
export function parsePackageManager(spec: string): PackageManagerSpec {
    const groups = PACKAGE_MANAGER_PATTERN.exec(spec.trim())?.groups as
        | PackageManagerGroups
        | undefined;

    if (!groups) {
        throw new Error(`Malformed packageManager field: ${spec}`);
    }

    return { name: groups.name, version: groups.version, hash: groups.hash || null };
}

/**
 * Serializes a {@linkcode PackageManagerSpec} back into a `packageManager` field.
 */
export function formatPackageManager({ name, version, hash }: PackageManagerSpec): string {
    return `${name}@${version}` + (hash ? `+${hash}` : "");
}

/**
 * Resolves the expected `sha512.<hex>` suffix for a `packageManager` pin.
 *
 * The npm registry publishes the tarball's integrity as base64 (`sha512-<base64>`),
 * while `packageManager` spells the same digest as hex.
 *
 * @param name The package manager's package name, e.g. `pnpm`.
 * @param version The exact version to look up.
 * @throws {Error} If the registry can't be reached, or the version isn't published.
 */
export async function resolvePackageManagerHash(name: string, version: string): Promise<string> {
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

    const manifest = (await response.json()) as { dist?: { integrity?: string } };
    const integrity = manifest.dist?.integrity;

    if (!integrity) {
        throw new Error(`Registry manifest for ${name}@${version} has no dist.integrity`);
    }

    const [algorithm, encoded] = integrity.split("-");

    if (!algorithm || !encoded) {
        throw new Error(
            `Registry manifest for ${name}@${version} has a malformed dist.integrity: ${integrity}`,
        );
    }

    return `${algorithm}.${Buffer.from(encoded, "base64").toString("hex")}`;
}

//#endregion
