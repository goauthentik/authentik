import { toAdminInterface } from "#elements/router/core/interfaces";

import {
    SidebarEntry,
    ExtendedSidebarItem,
    SidebarLicenseFlags,
    isSidebarAttributeObject,
    isEnterpriseEntry,
} from "#admin/sidebar/types";

import { msg } from "@lit/localize";

export { type ExtendedSidebarItem };

//#region Build Sidebar Struct

//  ___      _ _    _   ___ _    _     _                ___ _               _
// | _ )_  _(_) |__| | / __(_)__| |___| |__  __ _ _ _  / __| |_ _ _ _  _ __| |_
// | _ \ || | | / _` | \__ \ / _` / -_) '_ \/ _` | '_| \__ \  _| '_| || / _|  _|
// |___/\_,_|_|_\__,_| |___/_\__,_\___|_.__/\__,_|_|   |___/\__|_|  \_,_\__|\__|
//

export const ENTERPRISE_PATH = "/enterprise/licenses";

const enterpriseOnly = () =>
    msg("Enterprise only", {
        id: "sidebar.notice.enterprise-only",
    });

function makeSidebarEntry(entry: SidebarEntry, licensed: boolean, canEnterprise: boolean) {
    const [path, label, attributes, children]: SidebarEntry = entry;
    const enterprise = Boolean(!licensed && isEnterpriseEntry(attributes));
    const key = isSidebarAttributeObject(attributes) && attributes.key ? attributes.key : path;

    if (!key || key.trim().length === 0) {
        throw new Error("An entry must have either a path or a key");
    }

    if (!key || key.trim().length === 0) {
        throw new Error("An entry must have either a path or a key");
    }

    const item: ExtendedSidebarItem = {
        label,
        key,
        path: path ? toAdminInterface(enterprise ? ENTERPRISE_PATH : path) : null,
        enterprise,
    };

    if (enterprise) {
        item.notice = enterpriseOnly();
    }

    if (Array.isArray(children)) {
        item.children = resolveSidebarEntries(children, { licensed, canEnterprise });
    }

    if (isSidebarAttributeObject(attributes)) {
        if (attributes.expanded !== undefined) {
            item.expanded = attributes.expanded;
        }

        if (attributes.icon !== undefined) {
            item.icon = attributes.icon;
        }
    }

    if (Array.isArray(attributes)) {
        item.routes = attributes;
    }

    return item;
}

/**
 * Removes enterprise entries entirely if enterprise capability is not present, or marks them "as
 * enterprise" if they are but the product is unlicensed.
 */
export function resolveSidebarEntries(
    entries: readonly SidebarEntry[],
    { licensed, canEnterprise }: SidebarLicenseFlags,
): ExtendedSidebarItem[] {
    const isVisible = ([, , attributes]: SidebarEntry) =>
        canEnterprise || !isEnterpriseEntry(attributes);

    const visibleEntries = entries.filter(isVisible);

    return visibleEntries.map((entry) => makeSidebarEntry(entry, licensed, canEnterprise));
}

//#endregion

//#region Find Sidebar Entries

//  ___ _         _   ___ _    _     _                ___     _       _
// | __(_)_ _  __| | / __(_)__| |___| |__  __ _ _ _  | __|_ _| |_ _ _(_)___ ___
// | _|| | ' \/ _` | \__ \ / _` / -_) '_ \/ _` | '_| | _|| ' \  _| '_| / -_|_-<
// |_| |_|_||_\__,_| |___/_\__,_\___|_.__/\__,_|_|   |___|_||_\__|_| |_\___/__/
//

function findSidebarEntry(
    entries: readonly ExtendedSidebarItem[],
    predicate: (entry: ExtendedSidebarItem) => boolean,
): ExtendedSidebarItem | null {
    for (const entry of entries) {
        if (predicate(entry)) {
            return entry;
        }

        const found = entry.children ? findSidebarEntry(entry.children, predicate) : null;

        if (found) {
            return found;
        }
    }

    return null;
}

/**
 * The label of the entry that lists the given route, e.g. "Providers" for `provider-view`.
 */
export function findSidebarSectionByRoute(
    entries: readonly ExtendedSidebarItem[],
    routeName: string | null,
) {
    if (!routeName) {
        return null;
    }

    return findSidebarEntry(entries, ({ routes }) => !!routes?.includes(routeName))?.label ?? null;
}

export function findCurrentSidebarKey(
    entries: readonly ExtendedSidebarItem[],
    path: string,
    routeName: string | null,
) {
    const matches = ({ key, routes }: ExtendedSidebarItem) =>
        key === path || (!!routeName && !!routes?.includes(routeName));

    return findSidebarEntry(entries, matches)?.key ?? null;
}
