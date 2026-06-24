import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

import { collectDocFiles, normalizePath, parseDocFile, resolveDocumentUrl } from "./node.mjs";

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

test("parseDocFile uses frontmatter title and first paragraph for description", () => {
    const info = parseDocFile(resolve(FIXTURE, "topic-a/page-one.md"), FIXTURE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.title, "Page One"); // frontmatter title present
    assert.equal(info.description, "First real paragraph of page one.");
    assert.equal(info.path, "topic-a/page-one");
});

test("parseDocFile derives title from first heading when frontmatter has none", () => {
    const PARSE = resolve(__dirname, "__fixtures__", "parse");
    const info = parseDocFile(resolve(PARSE, "heading-only.md"), PARSE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.title, "Heading Title");
    assert.equal(info.description, "Heading-derived page body.");
});

test("parseDocFile returns null for draft files", () => {
    const PARSE = resolve(__dirname, "__fixtures__", "parse");
    assert.equal(parseDocFile(resolve(PARSE, "draft.md"), PARSE), null);
});

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
