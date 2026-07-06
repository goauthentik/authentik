/**
 * @file Hash / digest truncation (git SHAs, sha256, md5, opaque hex/base64).
 */

import { middleEllipsis, type TruncateOptions } from "./internal/primitives.js";

/**
 * Truncate an opaque digest, keeping a head-biased prefix (grep, cf. git short-SHA)
 * plus a tail for disambiguation.
 *
 * @param input The digest to truncate.
 */
export function truncateHash(input: string, options: TruncateOptions): string {
    return middleEllipsis(input, options, { headBias: 0.6 });
}
