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

/**
 * Parse `--min-length`: a positive integer.
 */
export function parseMinLength(value: string): number {
    const length = Number(value);

    if (!Number.isInteger(length) || length < 1) {
        throw new UsageError(`Invalid --min-length: ${value}`);
    }

    return length;
}
