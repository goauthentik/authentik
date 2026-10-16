/**
 * @file Reads one MDX page into search records. A heading starts a record, a table row whose
 *   first cell names something is a level-5 record, and paragraph and list text joins the record
 *   of the heading above it.
 *   Heading ids are computed the way Docusaurus computes them, with the same slugger and the same
 *   `{#custom-id}` parsing, so a record's anchor matches the rendered page.
 */

import { createHash } from "node:crypto";

import { inlinePartials } from "../llms-txt/markdown.mjs";
import { HIERARCHY_DEPTH, TABLE_ROW_LEVEL } from "./common.mjs";

import { createSlugger, escapeMarkdownHeadingIds, parseMarkdownHeadingId } from "@docusaurus/utils";
import remarkDirective from "remark-directive";
import remarkGfm from "remark-gfm";
import remarkMdx from "remark-mdx";
import remarkParse from "remark-parse";
import { unified } from "unified";

/**
 * @import { SearchRecord } from "./common.mjs";
 * @import { Root, RootContent, Heading, Table } from "mdast";
 */

/**
 * Headings whose section is a list of links to other pages.
 *
 * Each linked page is indexed under its own title, so the list yields no record.
 */
const LINK_LIST_HEADINGS = new Set(["related", "see also", "next"]);

/**
 * The deepest heading that starts a record of its own. A deeper heading's text joins the
 * section above it.
 *
 * The generated API changelog of a release page holds a heading per endpoint and per response
 * at `h5` and `h6`. As records of their own they would outnumber every other page's sections
 * and match any endpoint name; as the text of one changelog section they rank below a page
 * that is about the term.
 */
const MAX_RECORD_HEADING_LEVEL = 4;

/**
 * Docusaurus accepts HTML comments in MDX (`markdown.mdx1Compat.comments`) and renders nothing
 * for them; the MDX parser alone refuses them.
 */
const HTML_COMMENT = /<!--[\s\S]*?-->/g;

/**
 * Node types whose text belongs to no record: code is not prose, and an expression, an import or
 * raw HTML renders no reader-visible text of its own.
 */
const SILENT_TYPES = new Set([
    "code",
    "html",
    "image",
    "imageReference",
    "definition",
    "footnoteDefinition",
    "mdxjsEsm",
    "mdxFlowExpression",
    "mdxTextExpression",
    "thematicBreak",
    "yaml",
]);

/**
 * Strip MDX syntax from a page the MDX parser refused, so it can be read as plain Markdown.
 *
 * @param {string} content
 *
 * @returns {string}
 */
function stripMDX(content) {
    return content
        .replace(/^\s*(import|export)\s.*$/gm, "")
        .replace(/<\/?[A-Za-z][^>]*>/g, "")
        .replace(/\{[^}\n]*\}/g, "");
}

/**
 * @param {string} markdown
 * @param {boolean} mdx Whether to read MDX syntax. Off, JSX and expressions are plain text.
 *
 * @returns {Root}
 */
function parseTree(markdown, mdx) {
    const processor = unified().use(remarkParse).use(remarkGfm).use(remarkDirective);

    if (mdx) {
        processor.use(remarkMdx);
    }

    return processor.parse(markdown);
}

/**
 * The reader-visible text of a node and its descendants, whitespace collapsed.
 *
 * @param {import("unist").Node} node
 *
 * @returns {string}
 */
export function plainText(node) {
    return collectText(node).replace(/\s+/g, " ").trim();
}

/**
 * @param {import("unist").Node} node
 *
 * @returns {string}
 */
function collectText(node) {
    if (SILENT_TYPES.has(node.type)) return "";

    if ("value" in node && typeof node.value === "string") {
        return node.value;
    }

    if ("children" in node && Array.isArray(node.children)) {
        return node.children.map(collectText).join("");
    }

    return "";
}

/**
 * An explicit id from a trailing MDX comment holding `#my-id`, the second heading-id syntax
 * Docusaurus accepts beside `{#my-id}`.
 *
 * @param {Heading} heading
 *
 * @returns {string | undefined}
 */
function commentHeadingId(heading) {
    const last = heading.children.at(-1);

    if (!last || last.type !== "mdxTextExpression") return undefined;

    const match = /^\s*\/\*\s*#(\S+)/.exec(last.value);

    return match?.[1] || undefined;
}

/**
 * A row becomes its own record only when its first cell holds a name rather than a number or a
 * mark.
 *
 * @param {string} firstCell
 *
 * @returns {boolean}
 */
function namesRow(firstCell) {
    return /\p{L}/u.test(firstCell);
}

/**
 * @typedef {object} Draft
 * @property {string} anchor
 * @property {(string | null)[]} hierarchy
 * @property {number} level
 * @property {string[]} parts
 */

/**
 * @typedef {object} ExtractOptions
 * @property {string} site The label of the site the page belongs to.
 * @property {string} url The page's URL as stored in the index.
 * @property {string} category The page's top-level category label.
 * @property {string} title The page's title when its body holds no `h1`.
 * @property {string} filePath The page's absolute path, for resolving partial imports.
 * @property {(filePath: string, error: unknown) => void} [onFallback] Called when the MDX parser
 *   refuses the page and it is read as plain Markdown instead.
 */

/**
 * Read a page's body, without its frontmatter, into search records.
 *
 * @param {string} body
 * @param {ExtractOptions} options
 *
 * @returns {SearchRecord[]}
 */
export function extractRecords(body, options) {
    const inlined = escapeMarkdownHeadingIds(
        inlinePartials(body, options.filePath).replace(HTML_COMMENT, ""),
    );

    /** @type {Root} */
    let tree;

    try {
        tree = parseTree(inlined, true);
    } catch (error) {
        options.onFallback?.(options.filePath, error);
        tree = parseTree(stripMDX(inlined), false);
    }

    const slugger = createSlugger();

    /** @type {(string | null)[]} */
    const hierarchy = Array.from({ length: HIERARCHY_DEPTH }, () => null);

    hierarchy[0] = options.category;

    /** @type {Draft[]} */
    const drafts = [];
    let anchor = "";
    let titled = false;

    /** @type {Draft | null} */
    let section = null;

    /**
     * The page record holds the text above the first heading.
     *
     * @param {string} title
     */
    function startPage(title) {
        hierarchy[1] = title;
        hierarchy.fill(null, 2);
        section = { anchor: "", hierarchy: [...hierarchy], level: 1, parts: [] };
        drafts.push(section);
        titled = true;
    }

    /**
     * @param {Heading} heading
     */
    function visitHeading(heading) {
        const commentId = commentHeadingId(heading);
        const text = plainText(heading);
        const parsed = parseMarkdownHeadingId(text, "classic");
        const name = parsed.text.trim();
        const id = commentId ?? parsed.id ?? slugger.slug(name);

        if (heading.depth === 1 && !titled) {
            // The first `h1` is the page title. Its id is the page's own URL.
            // The slug is still consumed so a later heading with the same text differs.
            startPage(name);
            return;
        }

        const level = heading.depth;

        if (level > MAX_RECORD_HEADING_LEVEL) {
            if (section && name !== "") {
                section.parts.push(name);
            }

            return;
        }

        hierarchy[level] = name;
        hierarchy.fill(null, level + 1);
        anchor = id;

        if (level > 1 && LINK_LIST_HEADINGS.has(name.toLowerCase())) {
            section = null;
            return;
        }

        section = { anchor, hierarchy: [...hierarchy], level, parts: [] };
        drafts.push(section);
    }

    /**
     * @param {Table} table
     */
    function visitTable(table) {
        // The first row is the header.
        for (const row of table.children.slice(1)) {
            const cells = row.children.map(plainText);
            const first = cells[0];
            const last = cells.at(-1);

            if (first === undefined || last === undefined) continue;

            if (!namesRow(first)) {
                // A row keyed by a number or a mark joins the section's text instead of standing
                // as a hit.
                const text = cells.filter((cell) => cell !== "").join(" ");

                if (section && text !== "") {
                    section.parts.push(text);
                }

                continue;
            }

            const rowHierarchy = [...hierarchy];

            rowHierarchy[TABLE_ROW_LEVEL] = first;
            rowHierarchy.fill(null, TABLE_ROW_LEVEL + 1);

            drafts.push({
                anchor,
                hierarchy: rowHierarchy,
                level: TABLE_ROW_LEVEL,
                parts: cells.length > 1 ? [last] : [],
            });
        }
    }

    /**
     * @param {RootContent} node
     */
    function visit(node) {
        if (SILENT_TYPES.has(node.type)) return;

        if (node.type === "heading") {
            visitHeading(node);
            return;
        }

        if (node.type === "table") {
            visitTable(node);
            return;
        }

        if (node.type === "paragraph") {
            const text = plainText(node);

            if (section && text !== "") {
                section.parts.push(text);
            }

            return;
        }

        if ("children" in node) {
            for (const child of node.children) {
                visit(/** @type {RootContent} */ (child));
            }
        }
    }

    if (!tree.children.some((node) => node.type === "heading" && node.depth === 1)) {
        startPage(options.title);
    }

    for (const node of tree.children) {
        visit(node);
    }

    return drafts.map((draft, position) => ({
        id: createHash("sha256")
            .update(`${options.site}\n${options.url}#${draft.anchor}\n${position}`)
            .digest("hex")
            .slice(0, 32),
        site: options.site,
        url: options.url,
        anchor: draft.anchor,
        hierarchy: draft.hierarchy,
        content: draft.parts.join(" "),
        level: draft.level,
        position,
    }));
}
