import { build } from "./dist/node.js";

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(__dirname, ".");
const OUT_DIR = resolve(PACKAGE_ROOT, "dist");

const HEADER = `
/*
 * ⚠️  GENERATED FILE — do not edit directly.
 *
 * Source: packages/theme/lib/tokens/*.js
 * Builder:  packages/theme/scripts/build.mjs
 * Targets:
 *   - packages/theme/dist/index.css"
 *   - packages/theme/dist/tokens.dtcg.json"
 *   - packages/theme/dist/tokens.dtcg.resolver.json"
 */
`;

const { css } = await build();
import { mkdir, writeFile } from "node:fs/promises";

await writeFile(resolve(OUT_DIR, "index.css"), `${HEADER}\n\n${css}\s`, "utf-8");

