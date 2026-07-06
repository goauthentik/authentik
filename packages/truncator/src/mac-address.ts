/**
 * @file MAC address truncation — keep whole octets, drop the middle.
 */

import { segmentEllipsis, type TruncateOptions } from "./internal/primitives.js";

/**
 * Truncate a MAC address by dropping whole middle octets.
 * Supports `:` and `-` separators, preserving whichever the input uses.
 */
export function truncateMacAddress(input: string, options: TruncateOptions): string {
    const separator = input.includes("-") ? "-" : ":";

    return segmentEllipsis(input.split(separator), separator, options);
}
