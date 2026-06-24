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
