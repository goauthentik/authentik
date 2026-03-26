/** Humanize a tag by replacing separators and capitalizing words. */
export function formatTag(tag: string): string {
    return tag.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Tuple entries of group key and items. */
export type Grouped<T> = ReadonlyArray<readonly [string, T[]]>;

/** Group items by tag, assigning a default when none provided. */
export function groupByTag<T extends { tags?: ReadonlyArray<string> }>(
    items: ReadonlyArray<T>,
    defaultTag = "General",
): Grouped<T> {
    const groups: Record<string, T[]> = {};
    items.forEach((item) => {
        const tags = item.tags && item.tags.length ? item.tags : [defaultTag];
        tags.forEach((tag) => {
            if (!groups[tag]) groups[tag] = [];
            groups[tag].push(item);
        });
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
}

/** Group items by the first letter of their `term` property. */
export function groupByFirstLetter<T extends { term: string }>(
    items: ReadonlyArray<T>,
): Grouped<T> {
    const groups: Record<string, T[]> = {};
    items.forEach((item) => {
        const first = item.term.charAt(0).toUpperCase();
        if (!groups[first]) groups[first] = [];
        groups[first].push(item);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
}
