import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";

export interface GlossaryItem {
    id?: string;
    docId?: string;
    href?: string;
    type?: string;
    label?: string;
}

/**
 * Determines if the current path is within the glossary section
 */
export function isGlossaryPath(pathname: string): boolean {
    return /\/glossary(\/|$)/.test(pathname);
}

/**
 * Determines if a sidebar item is a glossary-related item that should be filtered out
 */
export function isGlossaryItem(item: PropSidebarItem | GlossaryItem): boolean {
    // Check if it's a link type with docId starting with 'glossary'
    if (item.type === "link" && "docId" in item && item.docId?.startsWith("glossary")) {
        return true;
    }

    // Check if it's a link type with href containing '/glossary/terms/'
    if (item.type === "link" && "href" in item && item.href?.includes("/glossary/terms/")) {
        return true;
    }

    // Check if it's a category with label 'terms' (for sidebar filtering)
    if (item.type === "category" && "label" in item && item.label === "terms") {
        return true;
    }

    return false;
}

/**
 * Filters out glossary items from a list of sidebar items
 */
export function filterGlossaryItems<T extends PropSidebarItem | GlossaryItem>(items: T[]): T[] {
    return items.filter((item) => !isGlossaryItem(item));
}
