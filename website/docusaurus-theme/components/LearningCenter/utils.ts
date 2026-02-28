/** Humanize a category by replacing separators and capitalizing words. */
export function formatCategory(category: string): string {
    return category.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Tuple entries of group key and items. */
export type Grouped<T> = ReadonlyArray<readonly [string, T[]]>;

/** Group resources by category. */
export function groupByCategory<T extends { category: string }>(
    items: ReadonlyArray<T>,
): Grouped<T> {
    const groups: Record<string, T[]> = {};
    items.forEach((item) => {
        const category = item.category || "General";
        if (!groups[category]) groups[category] = [];
        groups[category].push(item);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
}

/** Group resources by the first letter of their `resourceName` property. */
export function groupByFirstLetter<T extends { resourceName: string }>(
    items: ReadonlyArray<T>,
): Grouped<T> {
    const groups: Record<string, T[]> = {};
    items.forEach((item) => {
        const first = item.resourceName.charAt(0).toUpperCase();
        if (!groups[first]) groups[first] = [];
        groups[first].push(item);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
}
