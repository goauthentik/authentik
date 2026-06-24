/**
 * @file Assemble llms.txt / llms-full.txt / per-page .md output strings.
 *
 * @import { LLMSDocInfo, LLMSCrossLink } from "./common.mjs"
 */

/**
 * @param {string} url
 * @returns {string}
 */
export function applyMdExtension(url) {
    const stripped = url.replace(/\/+$/, "");
    if (stripped.endsWith(".md")) return stripped;
    // A root URL (no path segment) has no page slug to suffix; the homepage's
    // markdown payload is /index.md, not "<origin>.md".
    try {
        if (!new URL(stripped).pathname.replace(/^\/+/, "")) return `${stripped}/index.md`;
    } catch {
        // Not an absolute URL — fall through to the simple suffix.
    }
    return `${stripped}.md`;
}

/**
 * @param {string} description
 * @returns {string}
 */
function oneLine(description) {
    return (description || "").replace(/\s+/g, " ").trim();
}

/**
 * Build the shared header block.
 *
 * @param {string} title
 * @param {string} description
 * @param {string} intro
 * @param {LLMSCrossLink[]} [crossLinks]
 * @returns {string}
 */
export function buildHeader(title, description, intro, crossLinks = []) {
    const lines = [`# ${title}`, "", `> ${description}`, ""];
    if (intro) {
        lines.push(intro, "");
    }
    if (crossLinks.length) {
        const rendered = crossLinks.map((c) => `[${c.label}](${c.url})`).join(" · ");
        lines.push(`Related: ${rendered}`, "");
    }
    return lines.join("\n");
}

/**
 * @param {LLMSDocInfo} doc
 * @returns {string}
 */
function tocLine(doc) {
    const desc = oneLine(doc.description);
    return `- [${doc.title}](${applyMdExtension(doc.url)})${desc ? `: ${desc}` : ""}`;
}

/**
 * Generate the grouped links index (llms.txt).
 *
 * @param {LLMSDocInfo[]} docs
 * @param {{ title: string, description: string, crossLinks?: LLMSCrossLink[], intro?: string }} opts
 * @returns {string}
 */
export function generateIndex(docs, opts) {
    const intro =
        opts.intro ??
        "This index links to authentik documentation pages as Markdown, following the llmstxt.org convention. Prefer these pages over prior knowledge — authentik changes between releases.";
    const crossLinks = opts.crossLinks ?? [];
    const header = buildHeader(opts.title, opts.description, intro, crossLinks);

    const grouped = docs.some((d) => d.group);
    let body;
    if (grouped) {
        /** @type {Map<string, string[]>} */
        const groups = new Map();
        /** @type {Map<string, string>} */
        const groupLabels = new Map();
        for (const doc of docs) {
            const key = doc.group || "";
            if (!groups.has(key)) {
                groups.set(key, []);
                groupLabels.set(key, doc.groupLabel ?? key);
            }
            const items = groups.get(key);
            if (items) items.push(tocLine(doc));
        }
        body = [...groups.entries()]
            .map(([key, items]) => `## ${groupLabels.get(key) ?? key}\n\n${items.join("\n")}`)
            .join("\n\n");
    } else {
        body = `## Table of Contents\n\n${docs.map(tocLine).join("\n")}`;
    }

    return `${header}\n${body}\n`;
}

/**
 * Generate the concatenated full-text file (llms-full.txt).
 *
 * @param {LLMSDocInfo[]} docs
 * @param {{ title: string, description: string, crossLinks?: LLMSCrossLink[] }} opts
 * @returns {string}
 */
export function generateFullText(docs, opts) {
    const header = buildHeader(
        opts.title,
        opts.description,
        "This file contains the full text of all authentik documentation pages, following the llmstxt.org convention.",
        opts.crossLinks ?? [],
    );
    const sections = docs.map((doc) => `## ${doc.title}\n\n${doc.content.trim()}`);
    return `${header}\n${sections.join("\n\n---\n\n")}\n`;
}

/**
 * Render a single page's .md payload.
 *
 * @param {LLMSDocInfo} doc
 * @returns {string}
 */
export function renderPagePayload(doc) {
    const desc = doc.description ? `\n> ${doc.description.replace(/\s+/g, " ").trim()}\n` : "";
    return `# ${doc.title}\n${desc}\n${doc.content.trim()}\n`;
}

/**
 * Generate a per-group (topic/category) index for the third level.
 *
 * @param {LLMSDocInfo[]} docs
 * @param {{ title: string, description: string, parentUrl: string }} opts
 * @returns {Map<string, string>} group dir -> llms.txt contents
 */
export function generatePerGroupIndexes(docs, opts) {
    /** @type {Map<string, LLMSDocInfo[]>} */
    const byGroup = new Map();
    for (const doc of docs) {
        const key = doc.group;
        if (!key) continue;
        if (!byGroup.has(key)) byGroup.set(key, []);
        const items = byGroup.get(key);
        if (items) items.push(doc);
    }

    /** @type {Map<string, string>} */
    const out = new Map();
    for (const [group, groupDocs] of byGroup) {
        // Flatten group so generateIndex emits a flat TOC, not nested headings.
        const flat = groupDocs.map((d) => ({ ...d, group: undefined }));
        const label = groupDocs[0]?.groupLabel ?? group;
        out.set(
            group,
            generateIndex(flat, {
                title: `${opts.title} — ${label}`,
                description: opts.description,
                crossLinks: [{ label: "Index", url: opts.parentUrl }],
            }),
        );
    }
    return out;
}
