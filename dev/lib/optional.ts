/**
 * @file Load optional dependencies lazily so commands can run before `pnpm install`.
 */

import { existsSync } from "node:fs";
import { join } from "node:path";

import { ROOT } from "#dev/lib/git";

export const INSTALL_HINT = "Run `make install` (or `pnpm install`) at the repo root.";

function isMissingModule(error: unknown): boolean {
    return (error as { code?: string } | null)?.code === "ERR_MODULE_NOT_FOUND";
}

/**
 * Delegate a dynamic import error to `null` if the module is missing.
 *
 * Any other error is rethrown.
 */
export function delegateImportError(error: unknown): null {
    if (isMissingModule(error)) return null;
    throw error;
}

/**
 * Format a message indicating that a package isn't installed.
 */
export function formatPackageMissingMessage(pkg: string): string {
    return `\`${pkg}\` isn't installed. ${INSTALL_HINT}`;
}

/**
 * Whether `pkg` resolves from here, by Node's own resolution rules.
 */
export function resolvePackagePath(pkg: string): string | null {
    try {
        return import.meta.resolve(pkg);
    } catch {
        return null;
    }
}

/**
 * Whether `pkg` is linked into the root `node_modules`, read from disk on every call.
 *
 * For a process that waits for an install to finish: once `import.meta.resolve`
 * has failed for a package, it can keep failing in that process after the package is installed.
 */
export function isLinked(pkg: string): boolean {
    return existsSync(join(ROOT, "node_modules", pkg, "package.json"));
}
