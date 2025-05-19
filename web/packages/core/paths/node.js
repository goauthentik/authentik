import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const relativeDirname = dirname(fileURLToPath(import.meta.url));

/**
 * @typedef {'~authentik'} MonoRepoRoot
 */

/**
 * The root of the authentik monorepo.
 *
 * @runtime node
 */
export const MonoRepoRoot = /** @type {MonoRepoRoot} */ (
    resolve(relativeDirname, "..", "..", "..", "..")
);

/**
 * Resolve a package name to its location in the monorepo to the single node_modules directory.
 *
 * @param {string} packageName
 * @param {ImportMeta} [meta] The `import.meta` object of the module.
 *
 * @runtime node
 * @returns {string} The resolved path to the package.
 * @throws {Error} If the package cannot be resolved.
 */
export function resolvePackage(packageName, meta) {
    const require = createRequire(meta ? meta.url : import.meta.url);

    const relativePackageJSONPath = join(packageName, "package.json");

    /** @type {string} */
    let absolutePackageJSONPath;

    try {
        absolutePackageJSONPath = require.resolve(relativePackageJSONPath);
    } catch (cause) {
        const error = new Error(`🚫 Failed to resolve package "${packageName}"`);

        error.cause = cause;

        throw error;
    }

    return dirname(absolutePackageJSONPath);
}
