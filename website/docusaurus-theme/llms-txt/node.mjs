/* eslint-disable no-console */
/**
 * @file Pure node-side logic for the llms.txt plugin: discovery, parsing, URLs.
 *
 * @import { AKLlmsDocInfo } from "./common.mjs"
 */

import { resolve } from "node:path";

import { parseFileContentFrontMatter } from "@docusaurus/utils/lib/markdownUtils.js";
import { readFileSync } from "node:fs";
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
 * Extract a short description: frontmatter, else first prose paragraph.
 *
 * @param {Record<string, any>} frontMatter
 * @param {string} body
 * @returns {string}
 */
function extractDescription(frontMatter, body) {
    if (typeof frontMatter.description === "string" && frontMatter.description.trim()) {
        return frontMatter.description.trim();
    }
    for (const para of body.split("\n\n")) {
        const trimmed = para.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith("#")) continue;
        if (/^(import\s|export\s|:::|<)/.test(trimmed)) continue;
        return trimmed.replace(/\n/g, " ");
    }
    return "";
}

/**
 * Parse a single Markdown/MDX file into a doc record (url filled later).
 *
 * @param {string} filePath Absolute file path.
 * @param {string} baseDir Absolute scan root.
 * @returns {AKLlmsDocInfo | null}
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
    };
}
