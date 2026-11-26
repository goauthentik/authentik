/**
 * @file Load an installed dependency lazily, so commands that don't need it work before
 *   `pnpm install`. The same approach as `pino` in packages/logger-js/lib/node.ts.
 */

export const INSTALL_HINT = "Run `make install` (or `pnpm install`) at the repo root.";

function isMissingModule(error: unknown): boolean {
    return (error as { code?: string } | null)?.code === "ERR_MODULE_NOT_FOUND";
}

/**
 * Settle a dynamic import to `null` when the package isn't installed, as in
 * `await import("pg").catch(missing)`. Any other failure is a real error and is rethrown.
 */
export function missing(error: unknown): null {
    if (isMissingModule(error)) return null;
    throw error;
}

/** Why something couldn't run, for a result's `unknown` list or a failed check. */
export function notInstalled(pkg: string): string {
    return `\`${pkg}\` isn't installed. ${INSTALL_HINT}`;
}

/** Whether `pkg` resolves from here, by Node's own resolution rules. */
export function isInstalled(pkg: string): boolean {
    try {
        import.meta.resolve(pkg);

        return true;
    } catch {
        return false;
    }
}
