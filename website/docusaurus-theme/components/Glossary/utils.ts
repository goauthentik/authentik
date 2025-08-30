/**
 * Minimal Markdown-to-HTML conversion used for definitions.
 * Escapes HTML, supports inline code, emphasis, links, bullet lists, and line breaks.
 */
export function mdToHtml(md?: string): string {
    if (!md) return "";
    let html = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    if (/^\s*-\s+/m.test(html)) {
        html = html
            .split(/\n{2,}/)
            .map((block) => {
                const lines = block.split(/\n/);
                if (lines.every((l) => /^\s*-\s+/.test(l))) {
                    const items = lines
                        .map((l) => l.replace(/^\s*-\s+/, "").trim())
                        .map((c) => `<li>${c}</li>`)
                        .join("");
                    return `<ul>${items}</ul>`;
                }
                return block.replace(/\n/g, "<br/>");
            })
            .join("\n");
    } else {
        html = html.replace(/\n/g, "<br/>");
    }
    return html;
}

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
