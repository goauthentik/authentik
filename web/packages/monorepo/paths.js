import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const relativeDirname = dirname(fileURLToPath(import.meta.url));

/**
 * @typedef {'~authentik'} MonoRepoRoot
 */

/**
 * The root of the authentik monorepo.
 */
// TODO: Revise when this package is moved to the monorepo's `packages/monorepo` directory.
export const MonoRepoRoot = /** @type {MonoRepoRoot} */ (
    resolve(relativeDirname, "..", "..", "..")
);

const require = createRequire(import.meta.url);

/**
 * Resolve a package name to its location in the monorepo to the single node_modules directory.
 * @param {string} packageName
 *
 * @returns {string} The resolved path to the package.
 * @throws {Error} If the package cannot be resolved.
 */
export function resolvePackage(packageName) {
    const relativePackageJSONPath = join(packageName, "package.json");

    /** @type {string} */
    let absolutePackageJSONPath;

    try {
        absolutePackageJSONPath = require.resolve(relativePackageJSONPath);
    } catch (cause) {
        const error = new Error(`Failed to resolve package "${packageName}"`);

        error.cause = cause;

        throw error;
    }

    return dirname(absolutePackageJSONPath);
}
