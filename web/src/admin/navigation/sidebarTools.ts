import {
    SidebarEntry,
    ExtendedSidebarItem,
    SidebarLicenseFlags,
    isSidebarAttributeObject,
    isEnterpriseEntry,
} from "./types";

import { toAdminInterface } from "#elements/router/core/interfaces";

import { msg } from "@lit/localize";

export { type ExtendedSidebarItem };

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
        console.log(path, label, attributes, children);

        throw new Error("An entry must have either a path or a key");
    }

    const item: ExtendedSidebarItem = {
        label,
        key,
        path: path
            ? toAdminInterface(enterprise ? ENTERPRISE_PATH : (path ?? undefined))
            : null,
        enterprise,
    };

    if (enterprise) {
        item.notice = enterpriseOnly();
    }

    if (children) {
        item.children = resolveSidebarEntries(children ?? [], { licensed, canEnterprise });
    }

    if (Array.isArray(attributes) && attributes.length > 0) {
        item.route = attributes[0];
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
    const isVisible = ([, , attributes]: SidebarEntry) => canEnterprise || !isEnterpriseEntry(attributes);
    const visibleEntries = entries.filter(isVisible)
    return visibleEntries.map((entry) => makeSidebarEntry(entry, licensed, canEnterprise));
}

/**
 * The label of the entry that lists the given route, e.g. "Providers" for `provider-view`.
 */
export function findSidebarSectionByRoute(
    entries: readonly ExtendedSidebarItem[],
    routeName: string | null,
): string | null {
    if (!routeName) return null;

    for (const { label, children, route } of entries) {
        if (route && route === routeName) {
            return label;
        }

        const childLabel = children ? findSidebarSectionByRoute(children, routeName) : null;

        if (childLabel) return childLabel;
    }

    return null;
}
