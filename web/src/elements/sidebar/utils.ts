import { ROUTE_SEPARATOR } from "@goauthentik/common/constants";

import { SidebarEntry } from "./types";

export function entryKey(entry: SidebarEntry) {
    return `${entry.path || "no-path"}:${entry.label}`;
}

// "Never store what you can calculate." (At least, if it's cheap.)

/**
 * Takes tree and creates a map where every key is an entry in the tree and every value is that
 * entry's parent.
 */

export function makeParentMap(entries: SidebarEntry[]) {
    const reverseMap = new WeakMap<SidebarEntry, SidebarEntry>();
    function reverse(entry: SidebarEntry) {
        (entry.children ?? []).forEach((e) => {
            reverseMap.set(e, entry);
            reverse(e);
        });
    }
    entries.forEach(reverse);
    return reverseMap;
}

/**
 * Given the current path and the collection of entries, identify which entry is currently live.
 *
 */

const trailingSlash = new RegExp("/$");
const fixed = (s: string) => s.replace(trailingSlash, "");

function scanner(entry: SidebarEntry, activePath: string): SidebarEntry | undefined {
    if (typeof entry.path === "string" && fixed(activePath) === fixed(entry.path)) {
        return entry;
    }

    for (const matcher of entry.attributes?.activeWhen ?? []) {
        const matchtest = new RegExp(matcher);
        if (matchtest.test(activePath)) {
            return entry;
        }
    }

    return (entry.children ?? []).find((e) => scanner(e, activePath));
}

export function findMatchForNavbarUrl(entries: SidebarEntry[]) {
    const activePath = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR)[0];
    for (const entry of entries) {
        const result = scanner(entry, activePath);
        if (result) {
            return result;
        }
    }
    return undefined;
}
