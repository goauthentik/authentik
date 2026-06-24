/**
 * @file Assemble llms.txt / llms-full.txt / per-page .md output strings.
 *
 * @import { AKLlmsDocInfo, AKLlmsCrossLink } from "./common.mjs"
 */

/**
 * @param {string} url
 * @returns {string}
 */
export function applyMdExtension(url) {
    const stripped = url.replace(/\/+$/, "");
    return stripped.endsWith(".md") ? stripped : `${stripped}.md`;
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
 * @param {AKLlmsCrossLink[]} [crossLinks]
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
 * @param {AKLlmsDocInfo} doc
 * @returns {string}
 */
function tocLine(doc) {
    const desc = oneLine(doc.description);
    return `- [${doc.title}](${applyMdExtension(doc.url)})${desc ? `: ${desc}` : ""}`;
}

/**
 * Generate the grouped links index (llms.txt).
 *
 * @param {AKLlmsDocInfo[]} docs
 * @param {{ title: string, description: string, crossLinks?: AKLlmsCrossLink[], intro?: string }} opts
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
        for (const doc of docs) {
            const key = doc.group || "";
            if (!groups.has(key)) groups.set(key, []);
            const items = groups.get(key);
            if (items) items.push(tocLine(doc));
        }
        body = [...groups.entries()]
            .map(([label, items]) => `## ${label}\n\n${items.join("\n")}`)
            .join("\n\n");
    } else {
        body = `## Table of Contents\n\n${docs.map(tocLine).join("\n")}`;
    }

    return `${header}\n${body}\n`;
}

/**
 * Generate the concatenated full-text file (llms-full.txt).
 *
 * @param {AKLlmsDocInfo[]} docs
 * @param {{ title: string, description: string, crossLinks?: AKLlmsCrossLink[] }} opts
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
 * @param {AKLlmsDocInfo} doc
 * @returns {string}
 */
export function renderPagePayload(doc) {
    const desc = doc.description ? `\n> ${doc.description.replace(/\s+/g, " ").trim()}\n` : "";
    return `# ${doc.title}\n${desc}\n${doc.content.trim()}\n`;
}
