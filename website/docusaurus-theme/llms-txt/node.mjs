/**
 * @file Pure node-side logic for the llms.txt plugin: discovery, parsing, URLs.
 *
 * @import { LLMSDocInfo } from "./common.mjs"
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { trimTrailingSlashes } from "./common.mjs";

import { parseFileContentFrontMatter } from "@docusaurus/utils/lib/markdownUtils.js";
import FastGlob from "fast-glob";

/**
 * Convert OS path separators to POSIX.
 *
 * @param {string} p
 * @returns {string}
 */
export function normalizePath(p) {
    return p.split("\\").join("/");
}

/**
 * Glob all Markdown/MDX files under a directory, excluding partials and tests.
 *
 * @param {string} absDir Absolute directory to scan.
 * @param {string[]} [ignoreFiles] Extra glob patterns to exclude.
 * @returns {string[]} Absolute file paths.
 */
export function collectDocFiles(absDir, ignoreFiles = []) {
    const entries = FastGlob.sync("**/*.{md,mdx}", {
        cwd: absDir,
        onlyFiles: true,
        ignore: [
            "**/_*.{md,mdx}",
            "**/_*/**",
            "**/*.test.{md,mdx}",
            "**/__tests__/**",
            "**/__fixtures__/**",
            "**/node_modules/**",
            ...ignoreFiles,
        ],
    });

    return entries.map((rel) => resolve(absDir, rel));
}

/**
 * Extract the document title.
 *
 * @param {Record<string, any>} frontMatter
 * @param {string} body
 * @param {string} relPathNoExt
 * @returns {string}
 */
function extractTitle(frontMatter, body, relPathNoExt) {
    if (typeof frontMatter.title === "string" && frontMatter.title.trim()) {
        return frontMatter.title.trim();
    }
    const heading = body.match(/^#\s+(.+)$/m);
    if (heading && heading[1]) {
        return heading[1].trim();
    }
    const segments = relPathNoExt.split("/");
    return segments[segments.length - 1] || relPathNoExt;
}

/**
 * Normalize a description for use in an index line: strip blockquote markers,
 * `-- <source>` attribution lines, list bullets, and inline Markdown (links,
 * emphasis, code, images) down to their text, then collapse to a single line.
 * Integration pages often open with a blockquote citation, and other pages lead
 * with linked, bolded prose; both should read as plain text in the index.
 *
 * @param {string} text
 * @returns {string}
 */
function cleanDescriptionText(text) {
    return text
        .replace(/^\s*>\s?/gm, "") // blockquote markers
        .replace(/^\s*(--|—|–)\s.*$/gm, "") // "-- attribution" / em/en-dash source lines
        .replace(/^\s*[-*+]\s+/gm, "") // leading list bullets
        .replace(/!\[[^\]]*\]\([^)]*\)/g, "") // images
        .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1") // links -> link text
        .replace(/(\*\*|__)(.+?)\1/g, "$2") // bold
        .replace(/(\*|_)(.+?)\1/g, "$2") // italic
        .replace(/`([^`]+)`/g, "$1") // inline code
        .replace(/\s+/g, " ")
        .trim();
}

/**
 * Truncate cleaned prose to its first sentence so an extracted description is a
 * single clause rather than a long run-on. A terminal `.`/`!`/`?` must be
 * followed by whitespace or end-of-string, so decimals and abbreviations mid-word
 * don't split. Returns the input unchanged when no sentence terminator is found.
 *
 * @param {string} text
 * @returns {string}
 */
function firstSentence(text) {
    const match = text.match(/^.*?[.!?](?=\s|$)/);
    return match ? match[0].trim() : text;
}

/**
 * True when every non-empty line of a block is a list item. Such blocks are
 * prerequisite or feature enumerations, not a usable one-line description.
 *
 * @param {string} block
 * @returns {boolean}
 */
function isListBlock(block) {
    const lines = block
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
    return lines.length > 0 && lines.every((line) => /^([-*+]\s|\d+[.)]\s)/.test(line));
}

/**
 * Extract a short description: frontmatter, else the first usable prose
 * paragraph. Headings, MDX imports/exports, admonitions, JSX/HTML, CVE reporter
 * attributions, and bullet lists (prerequisites/feature enumerations) are
 * skipped so the description is a clean sentence, not a flattened block.
 *
 * @param {Record<string, any>} frontMatter
 * @param {string} body
 * @returns {string}
 */
function extractDescription(frontMatter, body) {
    if (typeof frontMatter.description === "string" && frontMatter.description.trim()) {
        return cleanDescriptionText(frontMatter.description);
    }
    for (const para of body.split("\n\n")) {
        const trimmed = para.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith("#")) continue; // headings
        if (/^(import\s|export\s)/.test(trimmed)) continue; // MDX imports/exports
        if (/^(:::|<)/.test(trimmed)) continue; // admonitions, JSX, HTML comments
        if (/^_*\s*reported by\b/i.test(trimmed)) continue; // CVE reporter attribution
        if (isListBlock(trimmed)) continue; // prerequisite/feature bullet lists
        return firstSentence(cleanDescriptionText(trimmed));
    }
    return "";
}

/**
 * Title-case a slug for display (e.g. "endpoint-devices" -> "Endpoint Devices").
 * A configured label (see {@link groupLabel}) overrides this for slugs whose
 * words need real expansion (e.g. "sys-mgmt" -> "System Management").
 *
 * Word boundaries come from any run of non-alphanumeric characters (`-`, `_`,
 * `/`, spaces), and accents are folded to ASCII so an accented directory name
 * degrades to letters rather than dropping them.
 *
 * @param {string} slug
 * @returns {string}
 */
function humanizeSlug(slug) {
    return slug
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "") // strip combining diacritics
        .replace(/[^a-zA-Z0-9]+/g, " ") // any separator run -> word boundary
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}

/**
 * Parse a single Markdown/MDX file into a doc record (url filled later).
 *
 * @param {string} filePath Absolute file path.
 * @param {string} baseDir Absolute scan root.
 * @returns {LLMSDocInfo | null}
 */
export function parseDocFile(filePath, baseDir) {
    const raw = readFileSync(filePath, "utf-8");
    const { frontMatter, content } = parseFileContentFrontMatter(raw);

    if (frontMatter.draft === true) {
        return null;
    }

    const relNoExt = normalizePath(filePath)
        .slice(normalizePath(baseDir).length + 1)
        .replace(/\.mdx?$/, "")
        .replace(/\/index$/, "");

    return {
        title: extractTitle(frontMatter, content, relNoExt),
        path: relNoExt,
        url: "",
        description: extractDescription(frontMatter, content),
        content,
        slug: typeof frontMatter.slug === "string" ? frontMatter.slug : undefined,
    };
}

/**
 * @param {string[]} routesPaths
 * @param {string} tail
 * @returns {string | undefined}
 */
function findMatchingRoute(routesPaths, tail) {
    const normalized = trimTrailingSlashes(tail.toLowerCase());
    if (!normalized) return undefined;

    const matches = routesPaths.filter((route) => {
        const r = trimTrailingSlashes(route.toLowerCase());
        return r === `/${normalized}` || r.endsWith(`/${normalized}`);
    });

    if (matches.length <= 1) return matches[0];
    return matches.sort((a, b) => a.length - b.length)[0];
}

/**
 * @param {string} urlPath
 * @returns {string}
 */
function collapseMatchingTrailingSegment(urlPath) {
    const segments = urlPath.split("/");
    if (segments.length >= 2) {
        const last = segments[segments.length - 1];
        const parent = segments[segments.length - 2];
        if (last && parent && last.toLowerCase() === parent.toLowerCase()) {
            return segments.slice(0, -1).join("/");
        }
    }
    return urlPath;
}

/**
 * @param {string} pathStr
 * @returns {string}
 */
function removeNumberedPrefixes(pathStr) {
    return pathStr
        .split("/")
        .map((segment) => segment.replace(/^\d+-/, ""))
        .join("/");
}

/**
 * Determine a doc's grouping key. Normally the directory slug (first path
 * segment); `regroup` lets a subtree split into its own group — e.g.
 * `["core/glossary", "glossary"]` pulls the glossary out of `## Core Concepts`
 * into its own `## Glossary` section.
 *
 * @param {{ path: string }} doc
 * @param {{ groupBy?: "topic"|"category", categories?: readonly (readonly [string,string])[],
 *   regroup?: readonly (readonly [string,string])[] }} opts
 * @returns {string}
 */
export function assignGroup(doc, opts) {
    if (opts.regroup) {
        for (const [prefix, slug] of opts.regroup) {
            if (doc.path === prefix || doc.path.startsWith(`${prefix}/`)) return slug;
        }
    }
    return doc.path.split("/")[0] || "";
}

/**
 * Resolve the human-readable display label for a group slug: a configured
 * `categories` label if present, otherwise a title-cased form of the slug.
 *
 * @param {string} group The group slug.
 * @param {{ groupBy?: "topic"|"category", categories?: readonly (readonly [string,string])[] }} opts
 * @returns {string}
 */
export function groupLabel(group, opts) {
    const found = opts.categories?.find(([dir]) => dir === group);
    if (found) return found[1];
    return humanizeSlug(group);
}

/**
 * Resolve a site-relative path to its rendered route URL.
 *
 * @param {string} relPathNoExt Site-relative path, POSIX, no extension.
 * @param {string[]} routesPaths Resolved routes from Docusaurus postBuild props.
 * @returns {string | undefined}
 */
export function resolveDocumentUrl(relPathNoExt, routesPaths) {
    if (!routesPaths || routesPaths.length === 0) return undefined;

    // The root index page has the bare path "index" (no leading "/index" to
    // strip), so it never suffix-matches a route. Map it to the site root.
    if (relPathNoExt === "" || relPathNoExt === "index") {
        return routesPaths.includes("/") ? "/" : undefined;
    }

    const tails = new Set([relPathNoExt]);
    tails.add(collapseMatchingTrailingSegment(relPathNoExt));
    tails.add(removeNumberedPrefixes(relPathNoExt));

    for (const tail of tails) {
        const match = findMatchingRoute(routesPaths, tail);
        if (match) return match;
    }
    return undefined;
}

/**
 * @param {string} routeBasePath
 * @returns {string}
 */
function normalizeRouteBasePath(routeBasePath) {
    if (!routeBasePath || routeBasePath === "/") {
        return "/";
    }

    let start = 0;
    let end = routeBasePath.length;
    while (start < end && routeBasePath[start] === "/") {
        start++;
    }
    while (end > start && routeBasePath[end - 1] === "/") {
        end--;
    }

    return `/${routeBasePath.slice(start, end)}/`;
}

/**
 * @param {string} routePath
 * @returns {string}
 */
function normalizeRoutePath(routePath) {
    const normalized = `/${routePath.replace(/^\/+/, "")}`.replace(/\/{2,}/g, "/");
    if (normalized === "/") {
        return normalized;
    }
    return normalized.endsWith("/") ? normalized : `${normalized}/`;
}

/**
 * Resolve a route from source metadata when Docusaurus' final route list is not
 * available, such as during the dev server's content loading phase.
 *
 * @param {LLMSDocInfo} doc
 * @param {string} routeBasePath
 * @returns {string}
 */
export function resolveDocumentUrlFromSource(doc, routeBasePath) {
    if (doc.slug) {
        if (doc.slug.startsWith("/")) {
            return normalizeRoutePath(doc.slug);
        }
        return normalizeRoutePath(`${normalizeRouteBasePath(routeBasePath)}${doc.slug}`);
    }

    if (doc.path === "" || doc.path === "index") {
        return normalizeRouteBasePath(routeBasePath);
    }

    return normalizeRoutePath(`${normalizeRouteBasePath(routeBasePath)}${doc.path}`);
}
