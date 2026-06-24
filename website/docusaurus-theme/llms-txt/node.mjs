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
