/**
 * @file Generic string truncation.
 */

import { endEllipsis, middleEllipsis, type TruncateOptions } from "./internal/primitives.js";

export type StringTruncateOptions = TruncateOptions & { mode?: "end" | "middle" };

/**
 * Truncate an arbitrary string. Defaults to end-ellipsis;
 * pass `mode: "middle"` to keep both ends.
 */
export function truncateString(input: string, options: StringTruncateOptions): string {
    if (options.mode === "middle") {
        return middleEllipsis(input, options);
    }

    return endEllipsis(input, options);
}
