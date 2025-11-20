/**
 * @file String utilities.
 */

import { msg, str } from "@lit/localize";

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

    const truncated = trimmed.substring(0, maxLength);

    return msg(str`${truncated}...`, {
        id: "truncated-content",
        desc: "A string that has been truncated to fit a certain length, ending with an ellipsis",
    });
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

    const truncated = array.slice(0, maxLength).join(" ");

    if (array.length > maxLength) {
        return msg(str`${truncated}...`, {
            id: "truncated-content",
            desc: "A string that has been truncated to fit a certain length, ending with an ellipsis",
        });
    }

    return truncated;
}
