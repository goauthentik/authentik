/**
 * @file Build script for `@goauthentik/theme`.
 *
 * Runs the styleframe transpiler against the configured token tree, then
 * writes two kinds of artefact:
 *
 *   - `index.css` — the entire theme as one self-contained file. styleframe
 *     already emits the whole token set as a single string, so this is just
 *     that string under the generated-file header. A theme is one semantic
 *     unit; shipping it as one syntactical file means consumers (and their
 *     bundlers) never have to resolve `@import` to adopt it.
 *   - One file per category (color, typography, spacing, shape, shadow,
 *     motion, z-index) for consumers who want to cherry-pick.
 *
 * Consumers can import the whole surface
 * (`@import "@goauthentik/theme/index.css"`) or cherry-pick a category
 * (`@import "@goauthentik/theme/color.css"`).
 *
 * Invoked by `npm run build:assets` and chained from `npm run build`.
 */

import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "../lib/node.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, "..");
const OUT_DIR = resolve(PACKAGE_ROOT, "dist");

/**
 * @typedef {object} Category
 * @property {string} name      Slug used for the output filename.
 * @property {string[]} prefixes
 *   Token-name prefixes (after the `--ak-` strip) that belong to this category.
 */

/** @type {Category[]} */
const CATEGORIES = [
    { name: "color", prefixes: ["color-"] },
    {
        name: "typography",
        prefixes: ["font-family-", "font-size-", "font-weight-", "line-height-"],
    },
    { name: "spacing", prefixes: ["space-"] },
    { name: "shape", prefixes: ["radius-", "border-width-"] },
    { name: "shadow", prefixes: ["shadow-"] },
    { name: "motion", prefixes: ["duration-", "easing-"] },
    { name: "z-index", prefixes: ["z-index-"] },
];

const HEADER = [
    "/*",
    " * ⚠️  GENERATED FILE — do not edit directly.",
    " *",
    " * Source: packages/theme/lib/tokens/*.js",
    " * Built:  packages/theme/scripts/build.mjs",
    " */",
    "",
].join("\n");

/**
 * One emitted block within the styleframe CSS output. `header` is the line
 * that opens the block (`:root {`, `@media (...) {`, `html[data-theme="..."] {`).
 * `prefix` is whitespace that should precede declarations inside the block,
 * preserved verbatim from the source. `closer` is the closing brace(s).
 *
 * @typedef {object} ParsedBlock
 * @property {string} header
 * @property {string[]} declarations
 * @property {string} closer
 */

/**
 * Split the styleframe CSS output into top-level blocks. Each block is one of:
 *
 *   :root { … }
 *   html[data-theme="…"] { … }
 *   @media (…) { :root { … } }
 *
 * Nested `:root` inside `@media` is preserved as part of the block — the
 * inner declarations are kept as a flat list and re-wrapped on emit.
 *
 * @param {string} css
 * @returns {ParsedBlock[]}
 */
function parseBlocks(css) {
    /** @type {ParsedBlock[]} */
    const blocks = [];

    // Top-level blocks separated by blank lines in styleframe's output.
    // Each block ends with a balanced closing brace at column zero. We don't
    // need a real CSS parser — the styleframe emitter is regular enough that
    // a small line-based state machine handles it.
    const lines = css.split("\n");
    let i = 0;

    while (i < lines.length) {
        while (i < lines.length && (lines[i] ?? "").trim() === "") i++;
        if (i >= lines.length) break;

        const opener = lines[i] ?? "";
        const header = opener.trim();
        if (!header.endsWith("{")) {
            i++;
            continue;
        }

        const openerIndent = opener.match(/^\s*/)?.[0] ?? "";
        i++;
        /** @type {string[]} */
        const innerLines = [];
        while (i < lines.length) {
            const line = lines[i] ?? "";
            const trimmed = line.trim();
            const indent = line.match(/^\s*/)?.[0] ?? "";
            if (trimmed === "}" && indent === openerIndent) {
                i++;
                break;
            }
            innerLines.push(line);
            i++;
        }

        blocks.push({
            header,
            declarations: innerLines,
            closer: "}",
        });
    }

    return blocks;
}

/**
 * Extract every `--ak-*: …;` declaration from a flat list of lines (which may
 * include a nested `:root { … }` wrapper from an `@media` block).
 *
 * @param {string[]} lines
 * @returns {string[]}
 */
function flattenDeclarations(lines) {
    return lines.filter((line) => /^\s*--ak-[a-z0-9-]+\s*:/.test(line));
}

/**
 * Build the CSS for one category by filtering each parsed block to that
 * category's declarations and re-wrapping them.
 *
 * @param {Category} category
 * @param {ParsedBlock[]} blocks
 */
function buildCategoryFile(category, blocks) {
    /** @param {string} line */
    const matches = (line) => {
        const declaration = line.match(/--ak-([a-z0-9-]+):/);
        if (!declaration || !declaration[1]) return false;
        const name = declaration[1];
        return category.prefixes.some((prefix) => name.startsWith(prefix));
    };

    /** @type {string[]} */
    const sections = [];

    for (const block of blocks) {
        if (block.header.startsWith("@media")) {
            // Drill into the inner `:root { … }` wrapper.
            const inner = flattenDeclarations(block.declarations).filter(matches);
            if (inner.length === 0) continue;
            sections.push(
                `${block.header}\n\t:root {\n${inner
                    .map((line) => "\t\t" + line.trim())
                    .join("\n")}\n\t}\n}`,
            );
            continue;
        }

        const filtered = block.declarations.filter(matches);
        if (filtered.length === 0) continue;
        sections.push(
            `${block.header}\n${filtered.map((line) => "\t" + line.trim()).join("\n")}\n}`,
        );
    }

    if (sections.length === 0) return null;
    return HEADER + sections.join("\n\n") + "\n";
}

/**
 * Build the self-contained index.css containing the whole theme. styleframe
 * already hands us the entire token set as one string, so index.css is that
 * string verbatim under the generated-file header — no `@import`, no assembly
 * for the consumer to undo. The per-category files remain for cherry-picking.
 *
 * @param {string} css
 */
function buildIndex(css) {
    return HEADER + css.replace(/^\n+/, "").trimEnd() + "\n";
}

await mkdir(OUT_DIR, { recursive: true });

const { css } = await build();
const blocks = parseBlocks(css);

const emitted = [];
for (const category of CATEGORIES) {
    const content = buildCategoryFile(category, blocks);
    if (content === null) {
        console.warn(`⚠️  No declarations found for category ${category.name}; skipping.`);
        continue;
    }
    await writeFile(resolve(OUT_DIR, `${category.name}.css`), content, "utf-8");
    emitted.push(category.name);
}

await writeFile(resolve(OUT_DIR, "index.css"), buildIndex(css), "utf-8");

console.log(
    `✅  Wrote dist/index.css (self-contained) + ${emitted.length} category files (${emitted.join(", ")})`,
);
