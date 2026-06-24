import { test } from "node:test";
import assert from "node:assert/strict";

import { applyMdExtension, generateIndex, buildHeader, generateFullText, renderPagePayload, generatePerGroupIndexes } from "./generate.mjs";

const DOCS = [
    { title: "Page One", url: "https://docs.x/topic-a/page-one/", description: "First.", group: "topic-a", path: "topic-a/page-one", content: "" },
    { title: "Page Two", url: "https://docs.x/topic-b/page-two/", description: "Second.", group: "topic-b", path: "topic-b/page-two", content: "" },
];

test("applyMdExtension appends .md once", () => {
    assert.equal(applyMdExtension("https://docs.x/a/b/"), "https://docs.x/a/b.md");
    assert.equal(applyMdExtension("https://docs.x/a/b.md"), "https://docs.x/a/b.md");
    assert.equal(applyMdExtension("https://docs.x/a/b"), "https://docs.x/a/b.md");
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

test("generateIndex emits a flat Table of Contents when no doc has a group", () => {
    const flat = [
        { title: "A", url: "https://docs.x/a/", description: "First.", path: "a", content: "" },
        { title: "B", url: "https://docs.x/b/", description: "", path: "b", content: "" },
    ];
    const out = generateIndex(flat, { title: "T", description: "D" });
    assert.ok(out.includes("## Table of Contents"), "flat TOC heading");
    assert.ok(!out.includes("## a"), "no group heading in flat mode");
    assert.ok(out.includes("- [A](https://docs.x/a.md): First."), "link with description");
    assert.ok(out.includes("- [B](https://docs.x/b.md)\n") || out.trimEnd().endsWith("- [B](https://docs.x/b.md)"), "empty-desc link omits the colon");
});

test("buildHeader renders title, description, intro, and related links", () => {
    const out = buildHeader("Title", "Desc", "Intro line.", [{ label: "X", url: "https://x/llms.txt" }]);
    assert.ok(out.startsWith("# Title\n"));
    assert.ok(out.includes("> Desc"));
    assert.ok(out.includes("Intro line."));
    assert.ok(out.includes("Related: [X](https://x/llms.txt)"));
});

test("buildHeader omits the Related line when there are no crossLinks", () => {
    const out = buildHeader("T", "D", "", []);
    assert.ok(!out.includes("Related:"));
});

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
    const doc = FULL[0];
    assert.ok(doc, "first doc must exist");
    const out = renderPagePayload(doc);
    assert.ok(out.startsWith("# Page One\n"));
    assert.ok(out.includes("> First."));
    assert.ok(out.includes("Body one."));
});

test("generatePerGroupIndexes makes one index per group with parent cross-link", () => {
    const map = generatePerGroupIndexes(DOCS, {
        title: "authentik Documentation",
        description: "Unified auth.",
        parentUrl: "https://docs.x/llms.txt",
    });
    assert.deepEqual([...map.keys()].sort(), ["topic-a", "topic-b"]);
    const a = map.get("topic-a");
    assert.ok(a, "topic-a index must exist");
    assert.ok(a.includes("# authentik Documentation — topic-a"));
    assert.ok(a.includes("[Index](https://docs.x/llms.txt)"));
    assert.ok(a.includes("[Page One]"));
    assert.ok(!a.includes("[Page Two]"));
});

test("generatePerGroupIndexes skips docs without a group", () => {
    const withUngrouped = [
        ...DOCS,
        { title: "Loose", url: "https://docs.x/loose/", description: "No group.", group: "", path: "loose", content: "" },
    ];
    const map = generatePerGroupIndexes(withUngrouped, {
        title: "authentik Documentation",
        description: "Unified auth.",
        parentUrl: "https://docs.x/llms.txt",
    });
    assert.deepEqual([...map.keys()].sort(), ["topic-a", "topic-b"]);
    for (const contents of map.values()) {
        assert.ok(!contents.includes("[Loose]"), "ungrouped doc never appears in any group index");
    }
});

test("generatePerGroupIndexes isolates each group's docs symmetrically", () => {
    const map = generatePerGroupIndexes(DOCS, {
        title: "authentik Documentation",
        description: "Unified auth.",
        parentUrl: "https://docs.x/llms.txt",
    });
    const b = map.get("topic-b");
    assert.ok(b, "topic-b index exists");
    assert.ok(b.includes("[Page Two]"), "topic-b includes its own doc");
    assert.ok(!b.includes("[Page One]"), "topic-b excludes topic-a's doc");
});
