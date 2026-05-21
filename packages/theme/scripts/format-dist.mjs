/**
 * @file Post-build prettier pass over `dist/`.
 *
 * Both the styleframe transpiler and the styleframe DTCG CLI emit valid but
 * not-particularly-pretty output (tab indentation, long lines that aren't
 * wrapped, mixed spacing in shadow values). Running prettier afterwards
 * gives anyone inspecting the published artefacts — `dist/index.css`,
 * `dist/color.css`, `dist/tokens.dtcg.json`, etc. — a consistent and
 * readable shape.
 *
 * Run as the last step of `npm run build` so every file consumers see is
 * formatted with the repository's own prettier config.
 */

import { readdir, readFile, writeFile } from "node:fs/promises";
import { extname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { AuthentikPrettierConfig } from "@goauthentik/prettier-config";

import prettier from "prettier";

const __dirname = resolve(fileURLToPath(import.meta.url), "..");
const PACKAGE_ROOT = resolve(__dirname, "..");
const DIST_DIR = resolve(PACKAGE_ROOT, "dist");

/** Parsers prettier should pick for each extension. */
const PARSER_BY_EXT = /** @type {const} */ ({
    ".css": "css",
    ".json": "json",
});

const entries = await readdir(DIST_DIR, { withFileTypes: true });
let formatted = 0;

for (const entry of entries) {
    if (!entry.isFile()) continue;
    const ext = extname(entry.name);
    const parser = PARSER_BY_EXT[/** @type {keyof typeof PARSER_BY_EXT} */ (ext)];
    if (!parser) continue;

    const path = resolve(DIST_DIR, entry.name);
    const raw = await readFile(path, "utf-8");
    const output = await prettier.format(raw, {
        ...AuthentikPrettierConfig,
        filepath: path,
        parser,
    });

    if (output !== raw) {
        await writeFile(path, output, "utf-8");
    }
    formatted++;
}

console.log(`✅  Formatted ${formatted} file(s) in dist/`);
