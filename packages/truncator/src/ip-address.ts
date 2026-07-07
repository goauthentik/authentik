/**
 * @file IP address truncation. IPv6 is canonicalized (RFC 5952)
 * before any ellipsizing; IPv4 keeps whole octets.
 */

import { middleEllipsis, segmentEllipsis, type TruncateOptions } from "./internal/primitives.js";

/**
 * Compress an IPv6 address per RFC 5952: lowercase, drop leading zeros in each
 * group, and collapse the longest run of all-zero groups (length >= 2) to "::".
 */
export function compressIPv6(value: string): string {
    let groups: string[];

    if (value.includes("::")) {
        const [left, right] = value.split("::");
        const leftGroups = left ? left.split(":") : [];
        const rightGroups = right ? right.split(":") : [];
        const missing = 8 - (leftGroups.length + rightGroups.length);
        groups = [...leftGroups, ...Array(Math.max(0, missing)).fill("0"), ...rightGroups];
    } else {
        groups = value.split(":");
    }

    groups = groups.map((group) => {
        const stripped = group.toLowerCase().replace(/^0+/, "");

        return stripped === "" ? "0" : stripped;
    });

    let bestStart = -1;
    let bestLen = 0;
    let curStart = -1;
    let curLen = 0;

    for (let i = 0; i < groups.length; i++) {
        if (groups[i] === "0") {
            if (curStart === -1) {
                curStart = i;
            }

            curLen++;

            if (curLen > bestLen) {
                bestLen = curLen;
                bestStart = curStart;
            }
        } else {
            curStart = -1;
            curLen = 0;
        }
    }

    if (bestLen >= 2) {
        const head = groups.slice(0, bestStart).join(":");
        const tail = groups.slice(bestStart + bestLen).join(":");

        return head + "::" + tail;
    }

    return groups.join(":");
}

/**
 * Truncate an IP address. IPv6 is compressed first; if it still doesn't fit it
 * is middle-ellipsized (when it contains "::") or group-ellipsized. IPv4 keeps
 * whole octets.
 */
export function truncateIPAddress(input: string, opts: TruncateOptions): string {
    if (input.includes(":")) {
        const compressed = compressIPv6(input);

        if (compressed.includes("::")) {
            return middleEllipsis(compressed, opts);
        }

        return segmentEllipsis(compressed.split(":"), ":", opts);
    }

    return segmentEllipsis(input.split("."), ".", opts);
}
