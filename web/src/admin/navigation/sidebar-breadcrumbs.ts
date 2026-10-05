import type { SidebarEntry } from "./types";

export type { SidebarEntry };

export interface SidebarBreadcrumb {
    label: string;
    path?: string;
}

function getSidebarEntryActiveWhen(attributes: SidebarEntry[2]): string[] {
    if (Array.isArray(attributes)) {
        return attributes;
    }

    return (attributes?.activeWhen as string[] | undefined) ?? [];
}

function sidebarEntryMatchesPath(
    path: string | null,
    attributes: SidebarEntry[2],
    activePath: string,
) {
    if (!path) {
        return false;
    }

    const entryPath = path.split(";")[0];
    const pathIsWholePath = new RegExp(`^${entryPath}$`).test(activePath);

    const pathIsAnActivePath = getSidebarEntryActiveWhen(attributes).some((pattern) =>
        new RegExp(pattern).test(activePath),
    );

    return pathIsWholePath || pathIsAnActivePath;
}

export function findSidebarBreadcrumbs(
    activePath: string,
    entries: readonly SidebarEntry[],
    parents: SidebarBreadcrumb[] = [],
): SidebarBreadcrumb[] {
    for (const [path, label, attributes, children] of entries) {
        const crumb = path ? { label, path } : { label };
        const crumbs = [...parents, crumb];

        if (sidebarEntryMatchesPath(path, attributes, activePath)) {
            return crumbs;
        }

        if (children) {
            const childCrumbs = findSidebarBreadcrumbs(activePath, children, crumbs);

            if (childCrumbs.length > 0) {
                return childCrumbs;
            }
        }
    }

    return [];
}
