#!/usr/bin/env node
// Postbuild step for the ESM output:
//
// 1. Walk dist/esm/**/*.js and append ".js" to extension-less relative
//    specifiers (e.g. `from "./runtime"` → `from "./runtime.js"`). The
//    typescript-fetch generator emits extension-less specifiers, which
//    `module: "ESNext"` does not rewrite. Without this fixup Node's
//    strict ESM resolver fails (`ERR_MODULE_NOT_FOUND`). Bundlers
//    accept either form.
//
// 2. Write dist/esm/package.json with `{ "type": "module" }` so the
//    nearest-package.json lookup tags the ESM artifacts as ESM even
//    though the root package declares `"type": "commonjs"`.

import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const esmDir = new URL("../dist/esm/", import.meta.url);
const root = new URL(esmDir).pathname;

const RELATIVE_SPECIFIER = /(\bfrom\s+["'])(\.{1,2}\/[^"']+?)(["'])/g;

function shouldRewrite(spec) {
    if (/\.(m?js|cjs|json)$/.test(spec)) return false;
    if (spec.endsWith("/")) return false;
    return true;
}

function rewrite(source) {
    return source.replace(RELATIVE_SPECIFIER, (match, prefix, spec, suffix) => {
        if (!shouldRewrite(spec)) return match;
        return `${prefix}${spec}.js${suffix}`;
    });
}

function walk(dir) {
    for (const entry of readdirSync(dir)) {
        const abs = join(dir, entry);
        const st = statSync(abs);
        if (st.isDirectory()) {
            walk(abs);
            continue;
        }
        if (!entry.endsWith(".js") && !entry.endsWith(".d.ts")) continue;
        const src = readFileSync(abs, "utf8");
        const next = rewrite(src);
        if (next !== src) writeFileSync(abs, next);
    }
}

walk(root);

writeFileSync(
    join(root, "package.json"),
    JSON.stringify({ type: "module", sideEffects: false }, null, 2) + "\n",
);
