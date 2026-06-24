# Layer 1 — `llms.txt` Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Docusaurus plugin to `@goauthentik/docusaurus-theme` that, at build time, emits a three-level llms.txt "index of indexes" plus per-page `.md` payloads for both the docs and integrations sites.

**Architecture:** A `postBuild` plugin (it needs Docusaurus's resolved `routesPaths` for accurate URLs). Pure logic lives in focused `.mjs` modules (discovery, URL resolution, MDX→Markdown cleaning, output generation), each unit-tested with `node --test`. `plugin.mjs` orchestrates them and writes files into the build's `outDir`. A `createLlmsPlugin` helper in `config.js` wires it into both site configs.

**Tech Stack:** Node ESM `.mjs` with JSDoc types (no TS build step — matches the package), `fast-glob`, `@docusaurus/utils` (`parseFileContentFrontMatter`), a `unified`/`remark` pipeline for MDX cleaning, `node:test` + `node:assert/strict`.

## Global Constraints

- Package: `@goauthentik/docusaurus-theme`, `"type": "module"`, **no build step** — ship source `.mjs`. (verbatim: `package.json` has no `scripts`.)
- Lang: JavaScript `.mjs` with JSDoc `@import`/`@param` type annotations. Match the style of `releases/plugin.mjs` and `releases/node.mjs`.
- Docusaurus: `^3.10.1` (so `props.routesPaths` IS available in `postBuild`).
- Test runner: `node --test` (root `website/package.json` `"test": "node --test"`). Test files: `*.test.mjs`.
- Frontmatter parsing: use `parseFileContentFrontMatter` from `@docusaurus/utils/lib/markdownUtils.js` (already used in `releases/node.mjs`). Do NOT add `gray-matter`.
- File discovery: use `fast-glob` (already a dependency).
- Lint: top each plugin/IO file with `/* eslint-disable no-console */` (matches `releases/plugin.mjs`); `console.log`/`warn` are the logging mechanism.
- Two sites, separate subdomains, both `baseUrl: "/"`: `https://docs.goauthentik.io`, `https://integrations.goauthentik.io`. Docs uses `routeBasePath: "/"`, `path: "."`. Integrations groups by `categories.mjs` (16 `[dirName, label]` pairs).
- All new code lives under `docusaurus-theme/llms-txt/`. Run targeted tests with explicit paths, e.g. `node --test docusaurus-theme/llms-txt/node.test.mjs` from the `website/` directory.

---

### Task 1: Scaffold `llms-txt/` module, types, exports, deps

**Files:**
- Create: `docusaurus-theme/llms-txt/common.mjs`
- Modify: `docusaurus-theme/package.json` (add `exports` entries + dependencies)
- Test: `docusaurus-theme/llms-txt/common.test.mjs`

**Interfaces:**
- Consumes: nothing.
- Produces: JSDoc typedefs imported by every later module — `AKLlmsDocsSection` `{ path: string, routeBasePath: string, label?: string }`, `AKLlmsPluginOptions` `{ siteUrl?: string, title?: string, description?: string, sections: AKLlmsDocsSection[], ignoreFiles?: string[], crossLinks?: {label: string, url: string}[], groupBy?: "topic"|"category", categories?: [string,string][] }`, `AKLlmsDocInfo` `{ title: string, path: string, url: string, description: string, content: string, group?: string }`. Also a runtime constant `LLMS_TXT_FILENAME = "llms.txt"`, `LLMS_FULL_FILENAME = "llms-full.txt"`.

- [ ] **Step 1: Write the failing test**

```js
// docusaurus-theme/llms-txt/common.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";

import { LLMS_TXT_FILENAME, LLMS_FULL_FILENAME, normalizeOptions } from "./common.mjs";

test("filename constants follow llmstxt.org convention", () => {
    assert.equal(LLMS_TXT_FILENAME, "llms.txt");
    assert.equal(LLMS_FULL_FILENAME, "llms-full.txt");
});

test("normalizeOptions applies defaults", () => {
    const opts = normalizeOptions({ sections: [{ path: ".", routeBasePath: "/" }] });
    assert.deepEqual(opts.ignoreFiles, []);
    assert.equal(opts.groupBy, "topic");
    assert.deepEqual(opts.crossLinks, []);
});

test("normalizeOptions throws without sections", () => {
    assert.throws(() => normalizeOptions({}), /sections/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/common.test.mjs`
Expected: FAIL — `Cannot find module './common.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// docusaurus-theme/llms-txt/common.mjs
/**
 * @file Types and option normalization for the llms.txt plugin.
 */

/**
 * @typedef {object} AKLlmsDocsSection
 * @property {string} path Filesystem path relative to siteDir (e.g. ".", "docs").
 * @property {string} routeBasePath Docusaurus routeBasePath for the section (e.g. "/").
 * @property {string} [label] Optional heading shown when grouping is flat.
 */

/**
 * @typedef {object} AKLlmsCrossLink
 * @property {string} label
 * @property {string} url
 */

/**
 * @typedef {object} AKLlmsPluginOptions
 * @property {string} [siteUrl] Overrides the site URL from Docusaurus config.
 * @property {string} [title] Overrides the site title.
 * @property {string} [description] Overrides the site tagline.
 * @property {AKLlmsDocsSection[]} sections One or more docs roots to scan.
 * @property {string[]} [ignoreFiles] Extra glob patterns to exclude.
 * @property {AKLlmsCrossLink[]} [crossLinks] Sibling-site links for the header.
 * @property {"topic"|"category"} [groupBy] How to group the root index.
 * @property {[string, string][]} [categories] [dirName, label] pairs (integrations).
 */

/**
 * @typedef {object} AKLlmsDocInfo
 * @property {string} title
 * @property {string} path Site-relative source path, POSIX separators, no extension.
 * @property {string} url Absolute URL of the rendered page.
 * @property {string} description
 * @property {string} content Cleaned Markdown body.
 * @property {string} [group] Topic dir or category label for grouping.
 */

export const LLMS_TXT_FILENAME = "llms.txt";
export const LLMS_FULL_FILENAME = "llms-full.txt";

/**
 * Validate and apply defaults to plugin options.
 *
 * @param {Partial<AKLlmsPluginOptions>} options
 * @returns {Required<Pick<AKLlmsPluginOptions, "sections" | "ignoreFiles" | "crossLinks" | "groupBy">> & AKLlmsPluginOptions}
 */
export function normalizeOptions(options) {
    if (!options || !Array.isArray(options.sections) || options.sections.length === 0) {
        throw new Error("llms.txt plugin requires a non-empty `sections` array.");
    }

    return {
        ...options,
        sections: options.sections,
        ignoreFiles: options.ignoreFiles ?? [],
        crossLinks: options.crossLinks ?? [],
        groupBy: options.groupBy ?? "topic",
    };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/common.test.mjs`
Expected: PASS (3 tests).

- [ ] **Step 5: Add package.json exports and dependencies**

In `docusaurus-theme/package.json`, add to `exports` (after the `releases/*` entries):

```json
        "./llms-txt/plugin": "./llms-txt/plugin.mjs",
        "./llms-txt/node": "./llms-txt/node.mjs",
        "./llms-txt/common": "./llms-txt/common.mjs"
```

And add to `dependencies` (keep alphabetical):

```json
        "@docusaurus/utils": "^3.10.1",
        "remark-directive": "^4.0.0",
        "remark-gfm": "^4.0.1",
        "remark-mdx": "^3.1.0",
        "remark-parse": "^11.0.0",
        "remark-stringify": "^11.0.0",
        "unified": "^11.0.5"
```

(`remark-directive`, `unist-util-visit`, `fast-glob` are already present.)

- [ ] **Step 6: Install and verify**

Run: `npm install` (from `website/`)
Expected: completes; `node --test docusaurus-theme/llms-txt/common.test.mjs` still PASS.

- [ ] **Step 7: Commit**

```bash
git add docusaurus-theme/llms-txt/common.mjs docusaurus-theme/llms-txt/common.test.mjs docusaurus-theme/package.json package-lock.json
git commit -m "feat(llms-txt): scaffold plugin module, types, and deps"
```

---

### Task 2: File discovery

**Files:**
- Create: `docusaurus-theme/llms-txt/node.mjs`
- Test: `docusaurus-theme/llms-txt/node.test.mjs`
- Create (fixtures): `docusaurus-theme/llms-txt/__fixtures__/site/topic-a/index.mdx`, `.../topic-a/page-one.md`, `.../topic-b/page-two.mdx`, `.../topic-b/_partial.mdx` (sibling of its importer so `./_partial.mdx` resolves)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `collectDocFiles(absDir: string, ignoreFiles?: string[]) => string[]` — absolute paths of `.md`/`.mdx` files under `absDir`, excluding partials (`_*`) and test files. `normalizePath(p: string) => string` — POSIX separators.

- [ ] **Step 1: Create fixtures**

```mdx
<!-- docusaurus-theme/llms-txt/__fixtures__/site/topic-a/index.mdx -->
---
title: Topic A Overview
description: The overview page for Topic A.
---

# Topic A Overview

Intro paragraph for topic A.
```

```md
<!-- docusaurus-theme/llms-txt/__fixtures__/site/topic-a/page-one.md -->
---
title: Page One
---

# Page One

First real paragraph of page one.
```

```mdx
<!-- docusaurus-theme/llms-txt/__fixtures__/site/topic-b/page-two.mdx -->
---
title: Page Two
description: Second page.
---

import Shared from "./_partial.mdx";

# Page Two

<Shared />

Body of page two.
```

```mdx
<!-- docusaurus-theme/llms-txt/__fixtures__/site/topic-b/_partial.mdx -->
Shared partial content.
```

- [ ] **Step 2: Write the failing test**

```js
// docusaurus-theme/llms-txt/node.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

import { collectDocFiles, normalizePath } from "./node.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE = resolve(__dirname, "__fixtures__", "site");

test("collectDocFiles finds md and mdx, excludes partials", () => {
    const files = collectDocFiles(FIXTURE).map((f) => normalizePath(f));
    const rels = files.map((f) => f.slice(normalizePath(FIXTURE).length + 1)).sort();
    assert.deepEqual(rels, ["topic-a/index.mdx", "topic-a/page-one.md", "topic-b/page-two.mdx"]);
});

test("collectDocFiles honors extra ignore patterns", () => {
    const files = collectDocFiles(FIXTURE, ["**/topic-b/**"]).map((f) => normalizePath(f));
    assert.ok(!files.some((f) => f.includes("topic-b")));
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/node.test.mjs`
Expected: FAIL — `Cannot find module './node.mjs'`.

- [ ] **Step 4: Write minimal implementation**

```js
// docusaurus-theme/llms-txt/node.mjs
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
```

Note: `readFileSync` / `parseFileContentFrontMatter` imports are used by Task 3; leaving them here keeps one import block. If your linter flags unused imports, add them in Task 3 instead.

- [ ] **Step 5: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/node.test.mjs`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add docusaurus-theme/llms-txt/node.mjs docusaurus-theme/llms-txt/node.test.mjs docusaurus-theme/llms-txt/__fixtures__
git commit -m "feat(llms-txt): add markdown file discovery"
```

---

### Task 3: Parse a doc file into `AKLlmsDocInfo`

**Files:**
- Modify: `docusaurus-theme/llms-txt/node.mjs`
- Test: `docusaurus-theme/llms-txt/node.test.mjs` (append)

**Interfaces:**
- Consumes: `normalizePath` (Task 2), `parseFileContentFrontMatter` (`@docusaurus/utils`).
- Produces: `parseDocFile(filePath: string, baseDir: string) => AKLlmsDocInfo | null` — returns `null` for `draft: true`. Sets `title` (frontmatter → first `#` heading → filename), `description` (frontmatter → first non-heading/non-import paragraph), `path` (site-relative, no extension, no trailing `/index`), `content` (raw body — cleaning happens in Task 5), and `url: ""` (filled in Task 4).

- [ ] **Step 1: Write the failing test (append)**

```js
import { parseDocFile } from "./node.mjs";

test("parseDocFile reads frontmatter title and description", () => {
    const info = parseDocFile(resolve(FIXTURE, "topic-a/index.mdx"), FIXTURE);
    assert.ok(info, "non-draft file parses to a record"); // also narrows away null
    assert.equal(info.title, "Topic A Overview");
    assert.equal(info.description, "The overview page for Topic A.");
    assert.equal(info.path, "topic-a"); // index collapses
});

test("parseDocFile falls back to first heading and first paragraph", () => {
    const info = parseDocFile(resolve(FIXTURE, "topic-a/page-one.md"), FIXTURE);
    assert.ok(info, "non-draft file parses to a record"); // also narrows away null
    assert.equal(info.title, "Page One"); // frontmatter title present
    assert.equal(info.description, "First real paragraph of page one.");
    assert.equal(info.path, "topic-a/page-one");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/node.test.mjs`
Expected: FAIL — `parseDocFile is not a function`.

- [ ] **Step 3: Write minimal implementation (append to node.mjs)**

```js
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/node.test.mjs`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/llms-txt/node.mjs docusaurus-theme/llms-txt/node.test.mjs
git commit -m "feat(llms-txt): parse docs into title/description/path records"
```

---

### Task 4: Resolve final page URL from `routesPaths`

**Files:**
- Modify: `docusaurus-theme/llms-txt/node.mjs`
- Test: `docusaurus-theme/llms-txt/node.test.mjs` (append)

**Interfaces:**
- Consumes: nothing new.
- Produces: `resolveDocumentUrl(relPathNoExt: string, routesPaths: string[]) => string | undefined` — suffix-matches the site-relative path against Docusaurus's resolved routes, trying the original tail, the collapsed-trailing-segment variant, and the numbered-prefix-stripped variant; returns the shortest matching route, else `undefined`.

- [ ] **Step 1: Write the failing test (append)**

```js
import { resolveDocumentUrl } from "./node.mjs";

const ROUTES = ["/", "/topic-a/", "/topic-a/page-one/", "/topic-b/page-two/"];

test("resolveDocumentUrl matches a route by suffix", () => {
    assert.equal(resolveDocumentUrl("topic-a/page-one", ROUTES), "/topic-a/page-one/");
});

test("resolveDocumentUrl strips numbered prefixes", () => {
    assert.equal(resolveDocumentUrl("topic-a/01-page-one", ROUTES), "/topic-a/page-one/");
});

test("resolveDocumentUrl returns undefined when no route matches", () => {
    assert.equal(resolveDocumentUrl("missing/page", ROUTES), undefined);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/node.test.mjs`
Expected: FAIL — `resolveDocumentUrl is not a function`.

- [ ] **Step 3: Write minimal implementation (append to node.mjs)**

```js
/**
 * @param {string[]} routesPaths
 * @param {string} tail
 * @returns {string | undefined}
 */
function findMatchingRoute(routesPaths, tail) {
    const normalized = tail.toLowerCase().replace(/\/+$/, "");
    if (!normalized) return undefined;

    const matches = routesPaths.filter((route) => {
        const r = route.toLowerCase().replace(/\/+$/, "");
        return r === `/${normalized}` || r.endsWith(`/${normalized}`);
    });

    if (matches.length <= 1) return matches[0];
    return matches.sort((a, b) => a.length - b.length)[0];
}

/**
 * @param {string} urlPath
 * @returns {string}
 */
function collapseMatchingTrailingSegment(urlPath) {
    const segments = urlPath.split("/");
    if (segments.length >= 2) {
        const last = segments[segments.length - 1];
        const parent = segments[segments.length - 2];
        if (last.toLowerCase() === parent.toLowerCase()) {
            return segments.slice(0, -1).join("/");
        }
    }
    return urlPath;
}

/**
 * @param {string} pathStr
 * @returns {string}
 */
function removeNumberedPrefixes(pathStr) {
    return pathStr
        .split("/")
        .map((segment) => segment.replace(/^\d+-/, ""))
        .join("/");
}

/**
 * Resolve a site-relative path to its rendered route URL.
 *
 * @param {string} relPathNoExt Site-relative path, POSIX, no extension.
 * @param {string[]} routesPaths Resolved routes from Docusaurus postBuild props.
 * @returns {string | undefined}
 */
export function resolveDocumentUrl(relPathNoExt, routesPaths) {
    if (!routesPaths || routesPaths.length === 0) return undefined;

    const tails = new Set([relPathNoExt]);
    tails.add(collapseMatchingTrailingSegment(relPathNoExt));
    tails.add(removeNumberedPrefixes(relPathNoExt));

    for (const tail of tails) {
        const match = findMatchingRoute(routesPaths, tail);
        if (match) return match;
    }
    return undefined;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/node.test.mjs`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/llms-txt/node.mjs docusaurus-theme/llms-txt/node.test.mjs
git commit -m "feat(llms-txt): resolve page URLs from Docusaurus routes"
```

---

### Task 5: MDX → clean Markdown (inline partials, strip directives)

**Files:**
- Create: `docusaurus-theme/llms-txt/markdown.mjs`
- Test: `docusaurus-theme/llms-txt/markdown.test.mjs`

**Interfaces:**
- Consumes: `parseFileContentFrontMatter`, the fixtures from Task 2 (`topic-b/page-two.mdx` imports `_partial.mdx`).
- Produces: `cleanMdxToMarkdown(content: string, filePath: string) => Promise<string>` — inlines `_*.mdx` partial imports, removes custom container directives (`:::ak-version`, `:::enterprise`, etc.) keeping their inner prose, drops `import`/`export` statements, and returns plain Markdown. Throws nothing: on a parse error it falls back to a regex pass so a single bad page never fails the build.

- [ ] **Step 1: Write the failing test**

```js
// docusaurus-theme/llms-txt/markdown.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { readFileSync } from "node:fs";

import { cleanMdxToMarkdown } from "./markdown.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE = resolve(__dirname, "__fixtures__", "site");

test("cleanMdxToMarkdown inlines a partial and drops the import", async () => {
    const file = resolve(FIXTURE, "topic-b/page-two.mdx");
    const raw = readFileSync(file, "utf-8");
    const out = await cleanMdxToMarkdown(raw, file);
    assert.ok(out.includes("Shared partial content."), "partial body inlined");
    assert.ok(!/^import\s/m.test(out), "import statement removed");
    assert.ok(!out.includes("<Shared"), "JSX tag removed");
});

test("cleanMdxToMarkdown strips a custom directive but keeps its text", async () => {
    const input = "# T\n\n:::ak-version[2024.1]\nAvailable since 2024.1\n:::\n\nBody.";
    const out = await cleanMdxToMarkdown(input, resolve(FIXTURE, "topic-a/page-one.md"));
    assert.ok(!out.includes(":::"), "directive markers removed");
    assert.ok(out.includes("Body."), "surrounding prose preserved");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/markdown.test.mjs`
Expected: FAIL — `Cannot find module './markdown.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// docusaurus-theme/llms-txt/markdown.mjs
/* eslint-disable no-console */
/**
 * @file Convert authentik MDX into clean Markdown for the .md payload:
 * inline partial imports, strip custom directives and JSX/imports.
 */

import { dirname, resolve } from "node:path";
import { readFileSync } from "node:fs";

import { parseFileContentFrontMatter } from "@docusaurus/utils/lib/markdownUtils.js";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkStringify from "remark-stringify";
import remarkMdx from "remark-mdx";
import remarkGfm from "remark-gfm";
import remarkDirective from "remark-directive";
import { visit } from "unist-util-visit";

/**
 * Regex fallback used when MDX parsing throws (malformed/complex JSX).
 *
 * @param {string} content
 * @returns {string}
 */
function regexClean(content) {
    return content
        .replace(/^\s*(import|export)\s.*$/gm, "")
        .replace(/^:::+.*$/gm, "")
        .replace(/<\/?[A-Z][^>]*>/g, "")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
}

/**
 * Read and recursively clean a partial file's body.
 *
 * @param {string} partialPath
 * @param {Set<string>} chain Guards against circular imports.
 * @returns {string}
 */
function loadPartial(partialPath, chain) {
    if (chain.has(partialPath)) return "";
    const raw = readFileSync(partialPath, "utf-8");
    const { content } = parseFileContentFrontMatter(raw);
    return content.trim();
}

/**
 * Inline `import X from "./_partial.mdx"` references, then return the body with
 * the import lines removed. JSX `<X />` usages are replaced with the body text.
 *
 * @param {string} content
 * @param {string} filePath
 * @returns {string}
 */
function inlinePartials(content, filePath) {
    const importRe = /^\s*import\s+(?:(\w+)|{\s*(\w+)\s*})\s+from\s+['"]([^'"]+_[^'"]+\.mdx?)['"];?\s*$/gm;
    /** @type {Map<string, string>} */
    const bodies = new Map();
    let match;
    while ((match = importRe.exec(content)) !== null) {
        const name = match[1] || match[2];
        const importPath = match[3];
        try {
            const partialPath = resolve(dirname(filePath), importPath);
            bodies.set(name, loadPartial(partialPath, new Set([filePath])));
        } catch (err) {
            console.warn(`llms-txt: failed to inline partial ${importPath}: ${err}`);
            bodies.set(name, "");
        }
    }

    let out = content.replace(importRe, "");
    for (const [name, body] of bodies) {
        const jsxRe = new RegExp(`<${name}\\s*(?:[^>]*?)(?:/>|>[\\s\\S]*?</${name}>)`, "g");
        out = out.replace(jsxRe, body);
    }
    return out;
}

/**
 * Convert authentik MDX to clean Markdown.
 *
 * @param {string} content Raw file content (may include frontmatter).
 * @param {string} filePath Absolute path (for resolving partials).
 * @returns {Promise<string>}
 */
export async function cleanMdxToMarkdown(content, filePath) {
    const { content: body } = parseFileContentFrontMatter(content);
    const inlined = inlinePartials(body, filePath);

    try {
        const file = await unified()
            .use(remarkParse)
            .use(remarkMdx)
            .use(remarkGfm)
            .use(remarkDirective)
            .use(stripNodesPlugin)
            .use(remarkStringify, { bullet: "-", fences: true })
            .process(inlined);
        return String(file).trim();
    } catch (err) {
        console.warn(`llms-txt: MDX parse failed for ${filePath}, using regex fallback: ${err}`);
        return regexClean(inlined);
    }
}

/**
 * Remark transformer: drop MDX/JSX and ESM nodes, unwrap directives to text.
 *
 * @returns {(tree: import("unist").Node) => void}
 */
function stripNodesPlugin() {
    return (tree) => {
        visit(tree, (node, index, parent) => {
            if (!parent || index === undefined) return;
            const t = node.type;
            if (
                t === "mdxjsEsm" ||
                t === "mdxFlowExpression" ||
                t === "mdxTextExpression" ||
                t === "mdxJsxFlowElement" ||
                t === "mdxJsxTextElement"
            ) {
                // Replace JSX containers with their text children, drop bare expr/esm.
                const kids = Array.isArray(node.children) ? node.children : [];
                parent.children.splice(index, 1, ...kids);
                return [visit.SKIP, index];
            }
            if (t === "containerDirective" || t === "leafDirective" || t === "textDirective") {
                const kids = Array.isArray(node.children) ? node.children : [];
                parent.children.splice(index, 1, ...kids);
                return [visit.SKIP, index];
            }
            return undefined;
        });
    };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/markdown.test.mjs`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/llms-txt/markdown.mjs docusaurus-theme/llms-txt/markdown.test.mjs
git commit -m "feat(llms-txt): clean MDX into Markdown (partials, directives)"
```

---

### Task 6: Generate the grouped index (`llms.txt`) string

**Files:**
- Create: `docusaurus-theme/llms-txt/generate.mjs`
- Test: `docusaurus-theme/llms-txt/generate.test.mjs`

**Interfaces:**
- Consumes: `AKLlmsDocInfo` (Task 1).
- Produces:
  - `applyMdExtension(url: string) => string` — strips trailing `/`, ensures a `.md` suffix.
  - `buildHeader(title: string, description: string, intro: string, crossLinks: {label,url}[]) => string`.
  - `generateIndex(docs: AKLlmsDocInfo[], opts: {title, description, crossLinks?}) => string` — groups by `doc.group` into `## Group` sections (flat `## Table of Contents` when no groups), each line `- [title](url.md): description`.

- [ ] **Step 1: Write the failing test**

```js
// docusaurus-theme/llms-txt/generate.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";

import { applyMdExtension, generateIndex } from "./generate.mjs";

const DOCS = [
    { title: "Page One", url: "https://docs.x/topic-a/page-one/", description: "First.", group: "topic-a", path: "topic-a/page-one", content: "" },
    { title: "Page Two", url: "https://docs.x/topic-b/page-two/", description: "Second.", group: "topic-b", path: "topic-b/page-two", content: "" },
];

test("applyMdExtension appends .md once", () => {
    assert.equal(applyMdExtension("https://docs.x/a/b/"), "https://docs.x/a/b.md");
    assert.equal(applyMdExtension("https://docs.x/a/b.md"), "https://docs.x/a/b.md");
});

test("generateIndex emits grouped sections with .md links and cross-links", () => {
    const out = generateIndex(DOCS, {
        title: "authentik Documentation",
        description: "Unified auth.",
        crossLinks: [{ label: "Integrations", url: "https://integrations.x/llms.txt" }],
    });
    assert.ok(out.startsWith("# authentik Documentation\n"));
    assert.ok(out.includes("> Unified auth."));
    assert.ok(out.includes("[Integrations](https://integrations.x/llms.txt)"));
    assert.ok(out.includes("## topic-a"));
    assert.ok(out.includes("- [Page One](https://docs.x/topic-a/page-one.md): First."));
    assert.ok(out.includes("## topic-b"));
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/generate.test.mjs`
Expected: FAIL — `Cannot find module './generate.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// docusaurus-theme/llms-txt/generate.mjs
/**
 * @file Assemble llms.txt / llms-full.txt / per-page .md output strings.
 *
 * @import { AKLlmsDocInfo, AKLlmsCrossLink } from "./common.mjs"
 */

/**
 * @param {string} url
 * @returns {string}
 */
export function applyMdExtension(url) {
    const stripped = url.replace(/\/+$/, "");
    return stripped.endsWith(".md") ? stripped : `${stripped}.md`;
}

/**
 * @param {string} description
 * @returns {string}
 */
function oneLine(description) {
    return (description || "").replace(/\s+/g, " ").trim();
}

/**
 * Build the shared header block.
 *
 * @param {string} title
 * @param {string} description
 * @param {string} intro
 * @param {AKLlmsCrossLink[]} [crossLinks]
 * @returns {string}
 */
export function buildHeader(title, description, intro, crossLinks = []) {
    const lines = [`# ${title}`, "", `> ${description}`, ""];
    if (intro) {
        lines.push(intro, "");
    }
    if (crossLinks.length) {
        const rendered = crossLinks.map((c) => `[${c.label}](${c.url})`).join(" · ");
        lines.push(`Related: ${rendered}`, "");
    }
    return lines.join("\n");
}

/**
 * @param {AKLlmsDocInfo} doc
 * @returns {string}
 */
function tocLine(doc) {
    const desc = oneLine(doc.description);
    return `- [${doc.title}](${applyMdExtension(doc.url)})${desc ? `: ${desc}` : ""}`;
}

/**
 * Generate the grouped links index (llms.txt).
 *
 * @param {AKLlmsDocInfo[]} docs
 * @param {{ title: string, description: string, crossLinks?: AKLlmsCrossLink[], intro?: string }} opts
 * @returns {string}
 */
export function generateIndex(docs, opts) {
    const intro =
        opts.intro ??
        "This index links to authentik documentation pages as Markdown, following the llmstxt.org convention. Prefer these pages over prior knowledge — authentik changes between releases.";
    const header = buildHeader(opts.title, opts.description, intro, opts.crossLinks ?? []);

    const grouped = docs.some((d) => d.group);
    let body;
    if (grouped) {
        /** @type {Map<string, string[]>} */
        const groups = new Map();
        for (const doc of docs) {
            const key = doc.group || "";
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(tocLine(doc));
        }
        body = [...groups.entries()]
            .map(([label, items]) => `## ${label}\n\n${items.join("\n")}`)
            .join("\n\n");
    } else {
        body = `## Table of Contents\n\n${docs.map(tocLine).join("\n")}`;
    }

    return `${header}\n${body}\n`;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/generate.test.mjs`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/llms-txt/generate.mjs docusaurus-theme/llms-txt/generate.test.mjs
git commit -m "feat(llms-txt): generate grouped llms.txt index"
```

---

### Task 7: Generate full-text (`llms-full.txt`) and per-page `.md`

**Files:**
- Modify: `docusaurus-theme/llms-txt/generate.mjs`
- Test: `docusaurus-theme/llms-txt/generate.test.mjs` (append)

**Interfaces:**
- Consumes: `buildHeader` (Task 6), `AKLlmsDocInfo` with `content` populated (cleaned in Task 5).
- Produces:
  - `generateFullText(docs, opts: {title, description, crossLinks?}) => string` — header + each doc as `## title` + cleaned content, joined by `\n\n---\n\n`.
  - `renderPagePayload(doc) => string` — a single page's `.md`: `# title` + `> description` + cleaned content.

- [ ] **Step 1: Write the failing test (append)**

```js
import { generateFullText, renderPagePayload } from "./generate.mjs";

const FULL = [
    { title: "Page One", url: "u1", description: "First.", content: "Body one.", path: "topic-a/page-one" },
    { title: "Page Two", url: "u2", description: "Second.", content: "Body two.", path: "topic-b/page-two" },
];

test("generateFullText concatenates with separators", () => {
    const out = generateFullText(FULL, { title: "All Docs", description: "Everything." });
    assert.ok(out.includes("## Page One\n\nBody one."));
    assert.ok(out.includes("\n---\n"));
    assert.ok(out.includes("## Page Two\n\nBody two."));
});

test("renderPagePayload renders a single page", () => {
    const out = renderPagePayload(FULL[0]);
    assert.ok(out.startsWith("# Page One\n"));
    assert.ok(out.includes("> First."));
    assert.ok(out.includes("Body one."));
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/generate.test.mjs`
Expected: FAIL — `generateFullText is not a function`.

- [ ] **Step 3: Write minimal implementation (append to generate.mjs)**

```js
/**
 * Generate the concatenated full-text file (llms-full.txt).
 *
 * @param {AKLlmsDocInfo[]} docs
 * @param {{ title: string, description: string, crossLinks?: AKLlmsCrossLink[] }} opts
 * @returns {string}
 */
export function generateFullText(docs, opts) {
    const header = buildHeader(
        opts.title,
        opts.description,
        "This file contains the full text of all authentik documentation pages, following the llmstxt.org convention.",
        opts.crossLinks ?? [],
    );
    const sections = docs.map((doc) => `## ${doc.title}\n\n${doc.content.trim()}`);
    return `${header}\n${sections.join("\n\n---\n\n")}\n`;
}

/**
 * Render a single page's .md payload.
 *
 * @param {AKLlmsDocInfo} doc
 * @returns {string}
 */
export function renderPagePayload(doc) {
    const desc = doc.description ? `\n> ${doc.description.replace(/\s+/g, " ").trim()}\n` : "";
    return `# ${doc.title}\n${desc}\n${doc.content.trim()}\n`;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/generate.test.mjs`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/llms-txt/generate.mjs docusaurus-theme/llms-txt/generate.test.mjs
git commit -m "feat(llms-txt): generate llms-full.txt and per-page payloads"
```

---

### Task 8: Per-group index generation (third level)

**Files:**
- Modify: `docusaurus-theme/llms-txt/generate.mjs`
- Test: `docusaurus-theme/llms-txt/generate.test.mjs` (append)

**Interfaces:**
- Consumes: `generateIndex` (Task 6).
- Produces: `generatePerGroupIndexes(docs, opts: {title, description, parentUrl}) => Map<string, string>` — keyed by group dir (`doc.group`), each value a `generateIndex` over only that group's docs, with a cross-link back up to `parentUrl` and title `"<title> — <group>"`.

- [ ] **Step 1: Write the failing test (append)**

```js
import { generatePerGroupIndexes } from "./generate.mjs";

test("generatePerGroupIndexes makes one index per group with parent cross-link", () => {
    const map = generatePerGroupIndexes(DOCS, {
        title: "authentik Documentation",
        description: "Unified auth.",
        parentUrl: "https://docs.x/llms.txt",
    });
    assert.deepEqual([...map.keys()].sort(), ["topic-a", "topic-b"]);
    const a = map.get("topic-a");
    assert.ok(a.includes("# authentik Documentation — topic-a"));
    assert.ok(a.includes("[Index](https://docs.x/llms.txt)"));
    assert.ok(a.includes("[Page One]"));
    assert.ok(!a.includes("[Page Two]"));
});
```

(Reuses the `DOCS` fixture array defined at the top of Task 6's test file.)

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/generate.test.mjs`
Expected: FAIL — `generatePerGroupIndexes is not a function`.

- [ ] **Step 3: Write minimal implementation (append to generate.mjs)**

```js
/**
 * Generate a per-group (topic/category) index for the third level.
 *
 * @param {AKLlmsDocInfo[]} docs
 * @param {{ title: string, description: string, parentUrl: string }} opts
 * @returns {Map<string, string>} group dir -> llms.txt contents
 */
export function generatePerGroupIndexes(docs, opts) {
    /** @type {Map<string, AKLlmsDocInfo[]>} */
    const byGroup = new Map();
    for (const doc of docs) {
        const key = doc.group;
        if (!key) continue;
        if (!byGroup.has(key)) byGroup.set(key, []);
        byGroup.get(key).push(doc);
    }

    /** @type {Map<string, string>} */
    const out = new Map();
    for (const [group, groupDocs] of byGroup) {
        // Flatten group so generateIndex emits a flat TOC, not nested headings.
        const flat = groupDocs.map((d) => ({ ...d, group: undefined }));
        out.set(
            group,
            generateIndex(flat, {
                title: `${opts.title} — ${group}`,
                description: opts.description,
                crossLinks: [{ label: "Index", url: opts.parentUrl }],
            }),
        );
    }
    return out;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/generate.test.mjs`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/llms-txt/generate.mjs docusaurus-theme/llms-txt/generate.test.mjs
git commit -m "feat(llms-txt): generate per-group third-level indexes"
```

---

### Task 9: Plugin orchestration (`postBuild`) + group assignment

**Files:**
- Modify: `docusaurus-theme/llms-txt/node.mjs` (add `assignGroup`)
- Create: `docusaurus-theme/llms-txt/plugin.mjs`
- Test: `docusaurus-theme/llms-txt/plugin.test.mjs`

**Interfaces:**
- Consumes: `collectDocFiles`, `parseDocFile`, `resolveDocumentUrl`, `normalizePath` (node.mjs); `cleanMdxToMarkdown` (markdown.mjs); `generateIndex`, `generateFullText`, `generatePerGroupIndexes`, `renderPagePayload`, `applyMdExtension` (generate.mjs); `normalizeOptions`, `LLMS_TXT_FILENAME`, `LLMS_FULL_FILENAME` (common.mjs).
- Produces:
  - `assignGroup(doc: AKLlmsDocInfo, opts) => string` — first path segment for `groupBy: "topic"`; for `"category"`, the label from `categories` keyed by first segment (falls back to the segment).
  - `buildLlmsOutputs(ctx) => Promise<Map<relPath, contents>>` — pure async core returning every file to write (root `llms.txt`, `llms-full.txt`, per-group `llms.txt`, per-page `.md`), keyed by build-relative output path. `ctx = { siteDir, outDir, siteUrl, title, description, options, routesPaths }`.
  - default export `akLlmsPlugin(loadContext, options)` — a `Plugin` whose `postBuild(props)` calls `buildLlmsOutputs` and writes the map to `outDir`.

- [ ] **Step 1: Write the failing test**

```js
// docusaurus-theme/llms-txt/plugin.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

import { buildLlmsOutputs, assignGroup } from "./plugin.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE = resolve(__dirname, "__fixtures__", "site");

const ROUTES = ["/", "/topic-a/", "/topic-a/page-one/", "/topic-b/page-two/"];

test("assignGroup uses first segment for topic grouping", () => {
    const doc = { path: "topic-a/page-one" };
    assert.equal(assignGroup(doc, { groupBy: "topic" }), "topic-a");
});

test("assignGroup maps category labels", () => {
    const doc = { path: "cloud-providers/aws" };
    assert.equal(
        assignGroup(doc, { groupBy: "category", categories: [["cloud-providers", "Cloud Providers"]] }),
        "Cloud Providers",
    );
});

test("buildLlmsOutputs emits root, full, per-group, and per-page files", async () => {
    const outputs = await buildLlmsOutputs({
        siteDir: FIXTURE,
        outDir: "/tmp/ignored",
        siteUrl: "https://docs.x",
        title: "authentik Documentation",
        description: "Unified auth.",
        routesPaths: ROUTES,
        options: { sections: [{ path: ".", routeBasePath: "/" }], groupBy: "topic", crossLinks: [] },
    });

    assert.ok(outputs.has("llms.txt"), "root index");
    assert.ok(outputs.has("llms-full.txt"), "full text");
    assert.ok(outputs.has("topic-a/llms.txt"), "per-group index");
    assert.ok(outputs.has("topic-a/page-one.md"), "per-page payload");

    const root = outputs.get("llms.txt");
    assert.ok(root.includes("## topic-a"));
    assert.ok(root.includes("(https://docs.x/topic-a/page-one.md)"));

    const page = outputs.get("topic-a/page-one.md");
    assert.ok(page.includes("First real paragraph of page one."));
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test docusaurus-theme/llms-txt/plugin.test.mjs`
Expected: FAIL — `Cannot find module './plugin.mjs'`.

- [ ] **Step 3: Add `assignGroup` to node.mjs**

```js
/**
 * Determine a doc's grouping key.
 *
 * @param {{ path: string }} doc
 * @param {{ groupBy?: "topic"|"category", categories?: [string,string][] }} opts
 * @returns {string}
 */
export function assignGroup(doc, opts) {
    const first = doc.path.split("/")[0] || "";
    if (opts.groupBy === "category" && Array.isArray(opts.categories)) {
        const found = opts.categories.find(([dir]) => dir === first);
        return found ? found[1] : first;
    }
    return first;
}
```

- [ ] **Step 4: Write plugin.mjs**

```js
// docusaurus-theme/llms-txt/plugin.mjs
/* eslint-disable no-console */
/**
 * @file Docusaurus llms.txt plugin (postBuild).
 *
 * @import { LoadContext, Plugin, Props } from "@docusaurus/types"
 * @import { AKLlmsPluginOptions, AKLlmsDocInfo } from "./common.mjs"
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";

import { LLMS_TXT_FILENAME, LLMS_FULL_FILENAME, normalizeOptions } from "./common.mjs";
import { collectDocFiles, parseDocFile, resolveDocumentUrl, assignGroup } from "./node.mjs";
import { cleanMdxToMarkdown } from "./markdown.mjs";
import {
    generateIndex,
    generateFullText,
    generatePerGroupIndexes,
    renderPagePayload,
    applyMdExtension,
} from "./generate.mjs";

const PLUGIN_NAME = "ak-llms-txt-plugin";

export { assignGroup };

/**
 * Build every output file's contents, keyed by build-relative path.
 *
 * @param {{ siteDir: string, outDir: string, siteUrl: string, title: string,
 *   description: string, routesPaths: string[], options: AKLlmsPluginOptions }} ctx
 * @returns {Promise<Map<string, string>>}
 */
export async function buildLlmsOutputs(ctx) {
    const options = normalizeOptions(ctx.options);

    /** @type {AKLlmsDocInfo[]} */
    const docs = [];

    for (const section of options.sections) {
        const absDir = path.resolve(ctx.siteDir, section.path);
        for (const file of collectDocFiles(absDir, options.ignoreFiles)) {
            const parsed = parseDocFile(file, absDir);
            if (!parsed) continue;

            const route = resolveDocumentUrl(parsed.path, ctx.routesPaths);
            if (!route) {
                console.warn(`${PLUGIN_NAME}: no route for ${parsed.path}, skipping.`);
                continue;
            }

            parsed.url = new URL(route, ctx.siteUrl).toString();
            parsed.group = assignGroup(parsed, options);
            parsed.content = await cleanMdxToMarkdown(parsed.content, file);
            docs.push(parsed);
        }
    }

    /** @type {Map<string, string>} */
    const outputs = new Map();

    const indexOpts = {
        title: ctx.title,
        description: ctx.description,
        crossLinks: options.crossLinks,
    };

    outputs.set(LLMS_TXT_FILENAME, generateIndex(docs, indexOpts));
    outputs.set(LLMS_FULL_FILENAME, generateFullText(docs, indexOpts));

    const rootUrl = new URL(`/${LLMS_TXT_FILENAME}`, ctx.siteUrl).toString();
    for (const [group, contents] of generatePerGroupIndexes(docs, {
        title: ctx.title,
        description: ctx.description,
        parentUrl: rootUrl,
    })) {
        outputs.set(`${group}/${LLMS_TXT_FILENAME}`, contents);
    }

    for (const doc of docs) {
        // applyMdExtension(url) gives the absolute .md URL; derive the build path.
        const rel = applyMdExtension(doc.url).slice(ctx.siteUrl.replace(/\/+$/, "").length + 1);
        outputs.set(rel, renderPagePayload(doc));
    }

    return outputs;
}

/**
 * @param {LoadContext} _loadContext
 * @param {AKLlmsPluginOptions} options
 * @returns {Plugin}
 */
function akLlmsPlugin(_loadContext, options) {
    return {
        name: PLUGIN_NAME,

        /**
         * @param {Props} props
         */
        async postBuild(props) {
            console.log(`🚀 ${PLUGIN_NAME} generating llms.txt`);

            const outputs = await buildLlmsOutputs({
                siteDir: props.siteDir,
                outDir: props.outDir,
                siteUrl: options.siteUrl ?? props.siteConfig.url,
                title: options.title ?? props.siteConfig.title,
                description: options.description ?? props.siteConfig.tagline ?? "",
                routesPaths: props.routesPaths,
                options,
            });

            await Promise.all(
                [...outputs.entries()].map(async ([rel, contents]) => {
                    const dest = path.join(props.outDir, rel);
                    await fs.mkdir(path.dirname(dest), { recursive: true });
                    await fs.writeFile(dest, contents, "utf-8");
                }),
            );

            console.log(`✅ ${PLUGIN_NAME} wrote ${outputs.size} files`);
        },
    };
}

export default akLlmsPlugin;
```

- [ ] **Step 5: Run test to verify it passes**

Run: `node --test docusaurus-theme/llms-txt/plugin.test.mjs`
Expected: PASS (3 tests).

- [ ] **Step 6: Run the whole suite**

Run: `node --test docusaurus-theme/llms-txt/*.test.mjs`
Expected: PASS (all tasks' tests green).

- [ ] **Step 7: Commit**

```bash
git add docusaurus-theme/llms-txt/plugin.mjs docusaurus-theme/llms-txt/node.mjs docusaurus-theme/llms-txt/plugin.test.mjs
git commit -m "feat(llms-txt): orchestrate generation in postBuild"
```

---

### Task 10: Wire into the docs build + validate end-to-end 🛑 GATE

**Files:**
- Modify: `docusaurus-theme/config.js` (add `createLlmsPlugin` helper)
- Modify: `docs/docusaurus.config.esm.mjs` (register the plugin)

**Interfaces:**
- Consumes: the published plugin export `@goauthentik/docusaurus-theme/llms-txt/plugin`.
- Produces: `createLlmsPlugin(options) => [string, AKLlmsPluginOptions]` — a plugin tuple for the Docusaurus `plugins` array.

- [ ] **Step 1: Add the helper to config.js**

Append to `docusaurus-theme/config.js`:

```js
/**
 * Create the llms.txt plugin tuple.
 *
 * @param {import("./llms-txt/common.mjs").AKLlmsPluginOptions} options
 * @returns {[string, import("./llms-txt/common.mjs").AKLlmsPluginOptions]}
 */
export function createLlmsPlugin(options) {
    return ["@goauthentik/docusaurus-theme/llms-txt/plugin", options];
}
```

- [ ] **Step 2: Register in the docs config**

In `docs/docusaurus.config.esm.mjs`, add `createLlmsPlugin` to the existing theme-config import:

```js
import {
    createAlgoliaConfig,
    createClassicPreset,
    createLlmsPlugin,
    extendConfig,
} from "@goauthentik/docusaurus-theme/config";
```

Then add to the `plugins` array (after the releases plugin tuple):

```js
            createLlmsPlugin({
                sections: [{ path: ".", routeBasePath: "/" }],
                groupBy: "topic",
                crossLinks: [
                    { label: "Integrations", url: "https://integrations.goauthentik.io/llms.txt" },
                ],
            }),
```

- [ ] **Step 3: Build the docs site**

Run: `npm run build -w docs`
Expected: build succeeds; console shows `🚀 ak-llms-txt-plugin generating llms.txt` and `✅ ak-llms-txt-plugin wrote N files`.

- [ ] **Step 4: Validate the output (GATE — index sanity + content quality)**

Run:
```bash
ls docs/build/llms.txt docs/build/llms-full.txt
sed -n '1,20p' docs/build/llms.txt
# Pick a real topic dir that exists in docs/ (e.g. add-secure-apps):
ls docs/build/add-secure-apps/llms.txt
```
Expected: root `llms.txt` has the title header, `Related: [Integrations]…`, and `## <topic>` sections with `(…page.md)` links; per-topic `llms.txt` exists; a sampled `.md` file (open one referenced in the index) contains clean prose with no `import` lines, no `:::` directives, and no leftover JSX badge components.

Manual check (the spec's content-quality gate): open 5 varied `.md` payloads and confirm an LLM could list the page's steps from them. If partials/directives leak, revisit Task 5 before continuing.

- [ ] **Step 5: Commit**

```bash
git add docusaurus-theme/config.js docs/docusaurus.config.esm.mjs
git commit -m "feat(llms-txt): enable on the docs build"
```

---

### Task 11: Wire into the integrations build (category grouping) 🛑 GATE

**Files:**
- Modify: `integrations/docusaurus.config.esm.mjs`

**Interfaces:**
- Consumes: `createLlmsPlugin` (Task 10), `integrations/categories.mjs` (the 16 `[dirName, label]` pairs).

- [ ] **Step 1: Import the helper and categories**

In `integrations/docusaurus.config.esm.mjs`, add `createLlmsPlugin` to the `@goauthentik/docusaurus-theme/config` import, and import the categories:

```js
import categories from "./categories.mjs";
```

(Confirm the existing import path/specifier for `config` matches the docs config; mirror it.)

- [ ] **Step 2: Register the plugin with category grouping**

Add to the integrations `plugins` array:

```js
            createLlmsPlugin({
                sections: [{ path: ".", routeBasePath: "/" }],
                groupBy: "category",
                categories,
                crossLinks: [
                    { label: "Documentation", url: "https://docs.goauthentik.io/llms.txt" },
                ],
            }),
```

- [ ] **Step 3: Build the integrations site**

Run: `npm run build -w integrations`
Expected: build succeeds; plugin logs appear.

- [ ] **Step 4: Validate (GATE)**

Run:
```bash
ls integrations/build/llms.txt integrations/build/llms-full.txt
ls integrations/build/cloud-providers/llms.txt
sed -n '1,30p' integrations/build/llms.txt
```
Expected: root `llms.txt` groups entries under human-readable category labels (e.g. `## Cloud Providers`), cross-links to docs, and a per-category `llms.txt` exists (e.g. `cloud-providers/llms.txt`) linking only that category's pages back up to the root index.

- [ ] **Step 5: Commit**

```bash
git add integrations/docusaurus.config.esm.mjs
git commit -m "feat(llms-txt): enable on the integrations build with category grouping"
```

---

## Self-Review

**1. Spec coverage (Layer 1 portion of `2026-06-24-authentik-llm-architecture-design.md`):**
- Three-level index (root + per-group + full-text): Tasks 6, 7, 8, 9. ✅
- Per-page `.md` as core payload: Tasks 7 (render) + 9 (emit). ✅
- Partial-import resolution + directive stripping via re-parsed MDX AST (the "re-parsing source" option the spec named): Task 5. ✅
- `postBuild` for route URLs: Tasks 4, 9. ✅
- `createLlmsPlugin` helper wired into both builds; integrations uses `categories.mjs`: Tasks 10, 11. ✅
- Lean option set (dropped blog/path-transform/customLLMFiles/keepFrontMatter): reflected in `AKLlmsPluginOptions` (Task 1). ✅
- Cross-link header ("each site links to its sibling"): `buildHeader`/`crossLinks` (Tasks 6, 10, 11). ✅
- The two spec validation gates (index sanity, content quality) and the integrations gate: Tasks 10, 11. ✅
- Out of scope here (Layers 2–3, the captcha pivot): correctly deferred to separate plans.

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code; every command shows expected output. ✅

**3. Type consistency:** `AKLlmsDocInfo` fields (`title/path/url/description/content/group`) used identically across Tasks 3/6/7/8/9. `generateIndex` opts shape consistent between Tasks 6 and 8. `applyMdExtension`/`buildHeader` defined in Task 6 and reused in 7/9. `assignGroup` defined in node.mjs (Task 9 step 3) and re-exported from plugin.mjs. ✅

**Known follow-ups (not blockers):** (a) the build-relative path derivation in Task 9 assumes `baseUrl: "/"` (true for both sites); if a site ever uses a non-root baseUrl, strip it explicitly. (b) If Task 10's content-quality gate shows `remark-mdx` choking on many real pages (regex fallback firing often), harden Task 5 — but ship the gate first to get evidence.
