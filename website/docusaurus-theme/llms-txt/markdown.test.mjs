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
