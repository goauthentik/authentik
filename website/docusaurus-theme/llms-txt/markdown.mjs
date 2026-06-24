// docusaurus-theme/llms-txt/markdown.mjs
/* eslint-disable no-console */
/**
 * @file Convert authentik MDX into clean Markdown for the .md payload:
 * inline partial imports, strip custom directives and JSX/imports.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

import { parseFileContentFrontMatter } from "@docusaurus/utils/lib/markdownUtils.js";
import remarkDirective from "remark-directive";
import remarkGfm from "remark-gfm";
import remarkMdx from "remark-mdx";
import remarkParse from "remark-parse";
import remarkStringify from "remark-stringify";
import { unified } from "unified";
import { SKIP, visit } from "unist-util-visit";

/**
 * Remove Docusaurus admonition fence markers (`:::note`, `:::info`, etc.,
 * including remark-escaped `\:::` forms and optional titles), keeping the
 * inner prose. Code-block-aware: never alters lines inside fenced code.
 *
 * @param {string} md
 * @returns {string}
 */
function stripAdmonitionFences(md) {
    const lines = md.split("\n");
    /** @type {string | null} */
    let fenceChar = null;
    const out = [];
    for (const line of lines) {
        const fence = line.match(/^\s*(`{3,}|~{3,})/);
        if (fence) {
            const ch = /** @type {string} */ (/** @type {string} */ (fence[1])[0]);
            if (fenceChar === null) {
                fenceChar = ch; // entering a code block
            } else if (ch === fenceChar) {
                fenceChar = null; // closing the code block
            }
            // else: different fence char inside a block — not a delimiter, leave fenceChar unchanged
            out.push(line);
            continue;
        }
        const inFence = fenceChar !== null;
        // Outside code: drop a line that is an admonition fence marker:
        //   opening `:::type[ ...title]` or `\:::type ...`, or a bare closing `:::` / `\:::`.
        if (!inFence && /^\s*\\?:::+\s*[a-zA-Z][\w-]*.*$/.test(line)) {
            continue; // opening fence (has a type word) — drop the marker line
        }
        if (!inFence && /^\s*\\?:::+\s*$/.test(line)) {
            continue; // bare closing fence — drop
        }
        out.push(line);
    }
    return out.join("\n").replace(/\n{3,}/g, "\n\n");
}

/**
 * Regex fallback used when MDX parsing throws (malformed/complex JSX).
 *
 * @param {string} content
 * @returns {string}
 */
function regexClean(content) {
    return stripAdmonitionFences(
        content
            .replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "")
            .replace(/^\s*(import|export)\s.*$/gm, "")
            .replace(/<\/?[A-Z][^>]*>/g, ""),
    ).trim();
}

/**
 * Read and recursively clean a partial file's body.
 *
 * @param {string} partialPath
 * @param {Set<string>} chain Guards against circular imports.
 * @returns {string}
 */
function loadPartial(partialPath, chain) {
    if (chain.has(partialPath)) return "";
    const raw = readFileSync(partialPath, "utf-8");
    const { content } = parseFileContentFrontMatter(raw);
    return content.trim();
}

/**
 * Inline `import X from "./_partial.mdx"` references, then return the body with
 * the import lines removed. JSX `<X />` usages are replaced with the body text.
 *
 * @param {string} content
 * @param {string} filePath
 * @returns {string}
 */
function inlinePartials(content, filePath) {
    const importRe =
        /^\s*import\s+(?:(\w+)|{\s*(\w+)\s*})\s+from\s+['"]([^'"]+_[^'"]+\.mdx?)['"];?\s*$/gm;
    /** @type {Map<string, string>} */
    const bodies = new Map();
    let match;
    while ((match = importRe.exec(content)) !== null) {
        const name = match[1] ?? match[2];
        const importPath = match[3];
        if (!name || !importPath) continue;
        try {
            // Markdown escapes leading underscores etc. in .md import paths (`\_partial.mdx`);
            // unescape before resolving so the partial file is actually found.
            const cleanImportPath = importPath.replace(/\\(?=[_*[\]()#-])/g, "");
            const partialPath = resolve(dirname(filePath), cleanImportPath);
            bodies.set(name, loadPartial(partialPath, new Set([filePath])));
        } catch (err) {
            console.warn(`llms-txt: failed to inline partial ${importPath}: ${err}`);
            bodies.set(name, "");
        }
    }

    let out = content.replace(importRe, "");
    for (const [name, body] of bodies) {
        const jsxRe = new RegExp(`<${name}\\s*(?:[^>]*?)(?:/>|>[\\s\\S]*?</${name}>)`, "g");
        out = out.replace(jsxRe, body);
    }
    return out;
}

/**
 * Convert authentik MDX to clean Markdown.
 *
 * @param {string} content Raw file content (may include frontmatter).
 * @param {string} filePath Absolute path (for resolving partials).
 * @param {(filePath: string, err: unknown) => void} [onFallback] Called when strict
 *   MDX parsing fails and the regex fallback is used (for caller-side summary logging).
 * @returns {Promise<string>}
 */
export async function cleanMdxToMarkdown(content, filePath, onFallback) {
    try {
        const { content: body } = parseFileContentFrontMatter(content);
        const inlined = inlinePartials(body, filePath);
        const file = await unified()
            .use(remarkParse)
            .use(remarkMdx)
            .use(remarkGfm)
            .use(remarkDirective)
            .use(stripNodesPlugin)
            .use(remarkStringify, { bullet: "-", fences: true })
            .process(inlined);
        return stripAdmonitionFences(String(file)).trim();
    } catch (err) {
        onFallback?.(filePath, err);
        return regexClean(content);
    }
}

/**
 * Remark transformer: drop MDX/JSX and ESM nodes, unwrap directives to text.
 *
 * @returns {(tree: import("mdast").Root) => void}
 */
function stripNodesPlugin() {
    return (/** @type {import("mdast").Root} */ tree) => {
        visit(tree, (node, index, parent) => {
            if (!parent || index === undefined) return;
            const t = node.type;
            /** @type {import("unist").Node[]} */
            const kids = Array.isArray(/** @type {any} */ (node).children)
                ? /** @type {any} */ (node).children
                : [];
            if (
                t === "mdxjsEsm" ||
                t === "mdxFlowExpression" ||
                t === "mdxTextExpression" ||
                t === "mdxJsxFlowElement" ||
                t === "mdxJsxTextElement"
            ) {
                // Replace JSX containers with their text children, drop bare expr/esm.
                /** @type {any} */ (parent).children.splice(index, 1, ...kids);
                return [SKIP, index];
            }
            if (t === "containerDirective" || t === "leafDirective" || t === "textDirective") {
                /** @type {any} */ (parent).children.splice(index, 1, ...kids);
                return [SKIP, index];
            }
            return undefined;
        });
    };
}
