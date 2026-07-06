/**
 * @file UUID truncation — keep whole hyphen-delimited segments.
 */

import { segmentEllipsis, type TruncateOptions } from "./internal/primitives.js";

/**
 * Truncate a UUID by dropping whole middle segments, keeping the first and last.
 */
export function truncateUUID(input: string, options: TruncateOptions): string {
    return segmentEllipsis(input.split("-"), "-", options);
}
