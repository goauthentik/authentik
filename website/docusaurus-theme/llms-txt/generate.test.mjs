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
