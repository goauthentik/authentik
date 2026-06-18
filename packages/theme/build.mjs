import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build } from "./dist/node.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, ".");
const OUT_DIR = resolve(PACKAGE_ROOT, "dist");

const HEADER = `
/*
 * ⚠️  GENERATED FILE — do not edit directly.
 *
 * Source:
 *   - packages/theme/src/tokens/*.js
 *   - packages/theme/src/font-face.css
 * Builder:  packages/theme/scripts/build.mjs
 * Targets:
 *   - packages/theme/dist/index.css"
 *   - packages/theme/dist/tokens.dtcg.json"
 *   - packages/theme/dist/tokens.dtcg.resolver.json"
 */
`;

const [css, staticContent] = await Promise.allSettled([
    build(),
    readFile(resolve(PACKAGE_ROOT, "src/font-face.css"), "utf-8"),
]);
await writeFile(resolve(OUT_DIR, "index.css"), `${HEADER}\n\n${css.css}\n${staticContent}\n`, "utf-8");
