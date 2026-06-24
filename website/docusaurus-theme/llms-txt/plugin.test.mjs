import assert from "node:assert/strict";
import { resolve } from "node:path";
// docusaurus-theme/llms-txt/plugin.test.mjs
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { assignGroup, buildLLMSOutputs, groupLabel } from "./plugin.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE = resolve(__dirname, "__fixtures__", "site");

const ROUTES = ["/", "/topic-a/", "/topic-a/page-one/", "/topic-b/page-two/"];

test("assignGroup uses first segment for topic grouping", () => {
    const doc = { path: "topic-a/page-one" };
    assert.equal(assignGroup(doc, { groupBy: "topic" }), "topic-a");
});

test("assignGroup returns the slug for category grouping (not the label)", () => {
    const doc = { path: "cloud-providers/aws" };
    assert.equal(
        assignGroup(doc, {
            groupBy: "category",
            categories: [["cloud-providers", "Cloud Providers"]],
        }),
        "cloud-providers",
    );
});

test("groupLabel resolves the display label from the slug", () => {
    assert.equal(
        groupLabel("cloud-providers", {
            groupBy: "category",
            categories: [["cloud-providers", "Cloud Providers"]],
        }),
        "Cloud Providers",
    );
});

test("buildLLMSOutputs emits root, full, per-group, and per-page files", async () => {
    const outputs = await buildLLMSOutputs({
        siteDir: FIXTURE,
        outDir: "/tmp/ignored",
        siteUrl: "https://docs.x",
        title: "authentik Documentation",
        description: "Unified auth.",
        routesPaths: ROUTES,
        options: {
            sections: [{ path: ".", routeBasePath: "/" }],
            groupBy: "topic",
            crossLinks: [],
        },
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

test("buildLLMSOutputs writes per-category index at the slug path with a label heading", async () => {
    const outputs = await buildLLMSOutputs({
        siteDir: FIXTURE,
        outDir: "/tmp/ignored",
        siteUrl: "https://x",
        title: "T",
        description: "D",
        routesPaths: ROUTES,
        options: {
            sections: [{ path: ".", routeBasePath: "/" }],
            groupBy: "category",
            categories: [["topic-a", "Topic A Label"]],
            crossLinks: [],
        },
    });
    assert.ok(outputs.has("topic-a/llms.txt"), "per-category index uses the SLUG path");
    assert.ok(![...outputs.keys()].some((k) => k.includes("Topic A Label")), "no label-named path");
    assert.ok(outputs.get("llms.txt")?.includes("## Topic A Label"), "root heading uses the LABEL");
});
