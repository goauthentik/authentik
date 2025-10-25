import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";

export interface GlossaryItem {
    id?: string;
    docId?: string;
    href?: string;
    type?: string;
    label?: string;
}

/**
 * Standardized term interface used by GlossaryHelper and DocCardList
 */
export interface GlossaryHelperTerm {
    id: string;
    term: string;
    shortDefinition: string;
    fullDefinition?: string;
    tags?: string[];
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

/**
 * Safely extracts string value from potentially undefined/mixed-type object property
 */
export function safeStringExtract(value: unknown, fallback: string = ""): string {
    return typeof value === "string" && value.trim().length > 0 ? value : fallback;
}

/**
 * Safely extracts string array from potentially undefined/mixed-type object property
 */
export function safeStringArrayExtract(value: unknown): string[] {
    return Array.isArray(value)
        ? value.filter((tag): tag is string => typeof tag === "string")
        : [];
}

/**
 * Extracts all available tags from a collection of terms
 */
export function extractAvailableTags(terms: readonly GlossaryHelperTerm[]): string[] {
    const tags = new Set<string>();
    terms.forEach((t) => {
        if (t.tags && t.tags.length) {
            t.tags.forEach((tag) => tags.add(tag));
        }
    });
    return Array.from(tags).sort();
}

/**
 * URL parameter utilities for glossary term selection
 */
export const glossaryUrlUtils = {
    /**
     * Gets the selected term ID from URL search params
     */
    getSelectedTermId: (searchParams: string): string => {
        const sp = new URLSearchParams(searchParams);
        return sp.get("term") || "";
    },

    /**
     * Creates URL search string with term parameter
     */
    createTermUrl: (currentSearch: string, termId: string): string => {
        const search = new URLSearchParams(currentSearch);
        search.set("term", termId);
        return `?${search.toString()}`;
    },
};

/**
 * Smooth scrolls to an element by ID if it exists
 */
export function scrollToElement(elementId: string): void {
    const el = document.getElementById(elementId);
    if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}
