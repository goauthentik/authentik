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

    const root = outputs.get("llms.txt") ?? "";
    assert.ok(root.includes("## topic-a"));
    assert.ok(root.includes("(https://docs.x/topic-a/page-one.md)"));

    const page = outputs.get("topic-a/page-one.md") ?? "";
    assert.ok(page.includes("First real paragraph of page one."));
});
