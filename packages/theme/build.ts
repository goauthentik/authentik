import console from "node:console";
import { writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "./dist/node.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, ".");
const OUT_DIR = resolve(PACKAGE_ROOT, "dist");

const HEADER = `/*
 * ⚠️  GENERATED FILE — do not edit directly.
 *
 * Source:   packages/theme/src/
 * Builder:  packages/theme/build.ts
 */
`;

interface Category {
    name: string;
    prefixes: string[];
}

const CATEGORIES: Category[] = [
    { name: "color", prefixes: ["global--color--"] },
    {
        name: "typography",
        prefixes: [
            "global--font-family--",
            "global--font-size--",
            "global--font-weight--",
            "global--line-height--",
        ],
    },
    { name: "spacing", prefixes: ["global--space--"] },
    { name: "shape", prefixes: ["global--radius--", "global--border-width--"] },
    { name: "shadow", prefixes: ["global--box-shadow--"] },
    { name: "motion", prefixes: ["global--duration--", "global--easing--"] },
    { name: "z-index", prefixes: ["global--z-index--"] },
];

/**
 * One emitted block within the styleframe CSS output. `header` is the line
 * that opens the block (`:root {`, `@media (...) {`, `html[data-theme="..."] {`).
 */
interface ParsedBlock {
    header: string;
    declarations: string[];
}

/**
 * Split the styleframe CSS output into top-level blocks. Each block is one of:
 *
 * :root { … }
 * html[data-theme="…"] { … }
 *
 * @media (…) { :root { … } }
 *
 * Nested `:root` inside `@media` is preserved as part of the block — the
 * inner declarations are kept as a flat list and re-wrapped on emit.
 */
function parseBlocks(css: string): ParsedBlock[] {
    const blocks: ParsedBlock[] = [];

    // Top-level blocks separated by blank lines in styleframe's output. Each
    // block ends with a balanced closing brace at column zero. We don't need a
    // real CSS parser — the styleframe emitter is regular enough that a small
    // line-based state machine handles it.
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
        const innerLines: string[] = [];
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

        blocks.push({ header, declarations: innerLines });
    }

    return blocks;
}

/**
 * Extract every `--ak-*: …;` declaration from a flat list of lines (which may
 * include a nested `:root { … }` wrapper from an `@media` block).
 */
function flattenDeclarations(lines: string[]): string[] {
    return lines.filter((line) => /^\s*--ak-[a-z0-9-]+\s*:/.test(line));
}

/**
 * Build the CSS for one category by filtering each parsed block to that
 * category's declarations and re-wrapping them. Returns null when no token in
 * the tree matches the category.
 */
function buildCategoryFile(category: Category, blocks: ParsedBlock[]): string | null {
    const matches = (line: string) => {
        const declaration = line.match(/--ak-([a-z0-9-]+):/);
        if (!declaration || !declaration[1]) return false;
        const name = declaration[1];
        return category.prefixes.some((prefix) => name.startsWith(prefix));
    };

    const sections: string[] = [];

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

const { css } = await build();

// index.css: every token in one file, resolving no `@import`. The typefaces the
// font-family tokens name live in @goauthentik/fonts — consumers load those
// faces themselves, so this package ships no font bytes and does not rebuild
// when they change.
await writeFile(resolve(OUT_DIR, "index.css"), `${HEADER}\n${css}\n`, "utf-8");

// Per-category files: lean slices for consumers that want to cherry-pick —
// e.g. the docs site pulling color + typography on their own.
const blocks = parseBlocks(css);
const emitted: string[] = [];
for (const category of CATEGORIES) {
    const content = buildCategoryFile(category, blocks);
    if (content === null) {
        console.warn(`⚠️  No declarations found for category ${category.name}; skipping.`);
        continue;
    }
    await writeFile(resolve(OUT_DIR, `${category.name}.css`), content, "utf-8");
    emitted.push(category.name);
}

console.log(
    `✅  Wrote dist/index.css (self-contained) + ${emitted.length} category files (${emitted.join(", ")})`,
);
