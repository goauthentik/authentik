import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const relativeDirname = dirname(fileURLToPath(import.meta.url));

export type MonoRepoRoot = "~authentik";

/**
 * The root of the authentik monorepo.
 *
 * @runtime node
 */
export const MonoRepoRoot = resolve(relativeDirname, "..", "..", "..", "..") as MonoRepoRoot;

/**
 * Resolve a package name to its location in the monorepo to the single node_modules directory.
 *
 * @param packageName The name of the package to resolve.
 * @param meta The `import.meta` object of the module.
 *
 * @runtime node
 * @returns The resolved path to the package.
 * @throws {Error} If the package cannot be resolved.
 */
export function resolvePackage(packageName: string, meta?: ImportMeta): string {
    const require = createRequire(meta ? meta.url : import.meta.url);

    const relativePackageJSONPath = join(packageName, "package.json");

    let absolutePackageJSONPath: string;

    try {
        absolutePackageJSONPath = require.resolve(relativePackageJSONPath);
    } catch (cause) {
        const error = new Error(`🚫 Failed to resolve package "${packageName}"`);

        error.cause = cause;

        throw error;
    }

    return dirname(absolutePackageJSONPath);
}
