import { ROUTE_SEPARATOR } from "@goauthentik/common/constants";

import { SidebarEntry } from "./types";

export function entryKey(entry: SidebarEntry) {
    return `${entry.path || "no-path"}:${entry.label}`;
}

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

function scanner(entry: SidebarEntry, activePath: string): SidebarEntry | undefined {
    for (const matcher of entry.attributes?.activeWhen ?? []) {
        const matchtest = new RegExp(matcher);
        if (matchtest.test(activePath)) {
            return entry;
        }
        const match: SidebarEntry | undefined = (entry.children ?? []).find((e) =>
            scanner(e, activePath),
        );
        if (match) {
            return match;
        }
    }
    return undefined;
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
