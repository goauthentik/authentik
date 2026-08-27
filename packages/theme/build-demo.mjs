/*
 * @file Build the theme demo
 */

import { copyFileSync, mkdirSync, readdirSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);

const DEMO_SRC_NAME = "demo";
const DEMO_DEST_NAME = "public";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, DEMO_DEST_NAME);
const FONTS_CSS = require.resolve("@goauthentik/fonts/faces.css");
const ICONS_CSS = require.resolve("@goauthentik/fonts/icons.css");
const TOKENS_CSS = join(HERE, "./dist/index.css");
const DEMO_SRC_PATH = join(HERE, DEMO_SRC_NAME);

const DEMO_SRCS = readdirSync(DEMO_SRC_PATH)
    .filter((filename) => /\.(html|css|js)$/.test(filename))
    .map((filename) => join(DEMO_SRC_PATH, filename));

/* It's a coincidence that the icons and font files are in the same folder. Don't rely on this in
 * the future.
 */
const FONT_PATH = dirname(FONTS_CSS);
const CSS_URL_RE = /url\("(\.\/[^"]+)"\)/g;

function findFontFiles() {
    let fontFiles = new Set();
    for (const sheet of [FONTS_CSS, ICONS_CSS]) {
        const css = readFileSync(sheet, "utf-8");
        const fontpaths = Array.from(css.matchAll(CSS_URL_RE));
        for (const [, path] of fontpaths) {
            fontFiles.add(path);
        }
    }
    if (!fontFiles.size) {
        throw new Error("Could not find font files.  Did you move them?");
    }
    return Array.from(fontFiles);
}

const fontFiles = findFontFiles();
mkdirSync(OUT, { recursive: true });
for (const fontFile of fontFiles) {
    const target = join(OUT, fontFile);
    mkdirSync(dirname(target), { recursive: true });
    copyFileSync(join(FONT_PATH, fontFile), target);
}

for (const source of [TOKENS_CSS, ICONS_CSS, FONTS_CSS, ...DEMO_SRCS]) {
    copyFileSync(source, join(OUT, basename(source)));
}
