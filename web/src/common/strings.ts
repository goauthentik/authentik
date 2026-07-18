/**
 * @file String utilities.
 */

import { msg } from "@lit/localize";

const truncationEllipsis = msg("...", {
    desc: "Truncation ellipsis",
    id: "ellipsis",
});

/**
 * Truncate a string based on character count.
 *
 * @see {@linkcode truncateWords}
 */
export function truncate(input?: string | null, maxLength = 10): string {
    const trimmed = input?.trim() ?? "";

    if (!trimmed || trimmed.length <= maxLength) {
        return trimmed;
    }

    return trimmed.substring(0, maxLength) + truncationEllipsis;
}

/**
 * Truncate a string based on maximum word count.
 *
 * @see {@linkcode truncate}
 *
 */
export function truncateWords(input?: string | null, maxLength = 10): string {
    const trimmed = input?.trim() ?? "";

    if (!trimmed || trimmed.length <= maxLength) {
        return trimmed;
    }

    const array = trimmed.split(" ");

    const ellipsis = array.length > maxLength ? truncationEllipsis : "";

    return array.slice(0, maxLength).join(" ") + ellipsis;
}
