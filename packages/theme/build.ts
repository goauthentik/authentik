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

const { css } = await build();

// index.css: every token in one file, resolving no `@import`. The typefaces the
// font-family tokens name live in @goauthentik/fonts — consumers load those
// faces themselves, so this package ships no font bytes and does not rebuild
// when they change.
await writeFile(resolve(OUT_DIR, "index.css"), `${HEADER}\n${css}\n`, "utf-8");

console.log(`✅  Wrote dist/index.css (self-contained)`);
