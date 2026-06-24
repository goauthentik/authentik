// docusaurus-theme/llms-txt/markdown.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { readFileSync } from "node:fs";

import { cleanMdxToMarkdown } from "./markdown.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE = resolve(__dirname, "__fixtures__", "site");
const FIXTURE_PARSE = resolve(__dirname, "__fixtures__", "parse");

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
    assert.ok(out.includes("Available since 2024.1"), "inner directive prose preserved");
});

test("cleanMdxToMarkdown falls back instead of throwing on malformed frontmatter", async () => {
    const input = "---\nfoo: [unclosed\n---\n\n# Title\n\nReal body text.";
    const out = await cleanMdxToMarkdown(input, resolve(FIXTURE, "topic-a/page-one.md"));
    assert.equal(typeof out, "string");
    assert.ok(out.includes("Real body text."), "body survives the fallback");
    assert.ok(!out.includes("foo: [unclosed"), "raw frontmatter is stripped in fallback");
});

test("cleanMdxToMarkdown strips admonition fences but keeps inner prose", async () => {
    const input = "# T\n\n:::info Heads up\nImportant note.\n:::\n\nAfter.";
    const out = await cleanMdxToMarkdown(input, resolve(FIXTURE, "topic-a/page-one.md"));
    assert.ok(!out.includes(":::"), "no admonition fence markers remain");
    assert.ok(!out.includes("\\:::"), "no escaped fence markers remain");
    assert.ok(out.includes("Important note."), "inner prose preserved");
    assert.ok(out.includes("After."), "following prose preserved");
});

test("cleanMdxToMarkdown preserves ::: inside fenced code blocks", async () => {
    const input = "# T\n\n```bash\naws s3 ls arn:::resource\n:::standalone-in-code\n```\n\nBody.";
    const out = await cleanMdxToMarkdown(input, resolve(FIXTURE, "topic-a/page-one.md"));
    assert.ok(out.includes("arn:::resource"), "inline ::: in code preserved");
    assert.ok(out.includes(":::standalone-in-code"), "::: line inside code fence preserved");
});

test("cleanMdxToMarkdown preserves ::: inside a ~~~ fenced block", async () => {
    const input = "# T\n\n~~~yaml\nkey: :::value\n~~~\n\nAfter.";
    const out = await cleanMdxToMarkdown(input, resolve(FIXTURE, "topic-a/page-one.md"));
    assert.ok(out.includes(":::value"), "::: inside ~~~ code fence preserved");
    assert.ok(out.includes("After."));
});

test("cleanMdxToMarkdown handles backticks nested in a ~~~ block without losing admonition stripping after it", async () => {
    const input = "# T\n\n~~~md\n```\ncode\n```\n~~~\n\n:::info\nNote body.\n:::\n\nEnd.";
    const out = await cleanMdxToMarkdown(input, resolve(FIXTURE, "topic-a/page-one.md"));
    // The inner ``` is inside the ~~~ block and must NOT close it; the :::info AFTER the block must still be stripped.
    assert.ok(!out.includes(":::info"), "admonition after a nested-fence block is still stripped");
    assert.ok(out.includes("Note body."), "admonition inner prose preserved");
    assert.ok(out.includes("End."));
});

test("cleanMdxToMarkdown inlines a partial whose import path has a Markdown-escaped underscore", async () => {
    const file = resolve(FIXTURE_PARSE, "escaped-import.md");
    const raw = readFileSync(file, "utf-8");
    const out = await cleanMdxToMarkdown(raw, file);
    assert.ok(out.includes("Escaped partial body."), "escaped-path partial is inlined");
    assert.ok(!/^import\s/m.test(out), "import line removed");
    assert.ok(!out.includes("\\_esc-note"), "no escaped path leaks");
});
