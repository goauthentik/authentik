import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

import { collectDocFiles, normalizePath, parseDocFile } from "./node.mjs";

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

test("parseDocFile reads frontmatter title and description", () => {
    const info = parseDocFile(resolve(FIXTURE, "topic-a/index.mdx"), FIXTURE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.title, "Topic A Overview");
    assert.equal(info.description, "The overview page for Topic A.");
    assert.equal(info.path, "topic-a"); // index collapses
});

test("parseDocFile falls back to first heading and first paragraph", () => {
    const info = parseDocFile(resolve(FIXTURE, "topic-a/page-one.md"), FIXTURE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.title, "Page One"); // frontmatter title present
    assert.equal(info.description, "First real paragraph of page one.");
    assert.equal(info.path, "topic-a/page-one");
});
