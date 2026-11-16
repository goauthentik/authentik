/**
 * @file Shared helpers for the CLI commands.
 */

import { canonicalizeLocale } from "#translation/locale";

export interface Command {
    /**
     * One line for the top-level help.
     */
    summary: string;
    usage: string;
    run(argv: string[]): Promise<void>;
}

export class UsageError extends Error {
    override name = "UsageError";
}

/**
 * Canonicalize locale tags given on the command line.
 */
export function parseLocaleTags(tags: readonly string[]): string[] {
    return tags.map((tag) => {
        const locale = canonicalizeLocale(tag);

        if (!locale) {
            throw new UsageError(`Invalid locale: ${tag}`);
        }

        return locale;
    });
}
