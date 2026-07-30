import assert from "node:assert/strict";
import { resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import {
    assignGroup,
    collectDocFiles,
    groupLabel,
    normalizePath,
    parseDocFile,
    resolveDocumentUrl,
    resolveDocumentUrlFromSource,
} from "./node.mjs";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const FIXTURE = resolve(__dirname, "__fixtures__", "site");

/**
 * @param {string} path
 * @param {string} [slug]
 * @returns {import("./common.mjs").LLMSDocInfo}
 */
function testDoc(path, slug) {
    return {
        title: "Test",
        path,
        url: "",
        description: "",
        content: "",
        slug,
    };
}

test("collectDocFiles finds md and mdx, excludes partials", () => {
    const files = collectDocFiles(FIXTURE).map((f) => normalizePath(f));
    const rels = files.map((f) => f.slice(normalizePath(FIXTURE).length + 1)).sort();
    assert.deepEqual(rels, [
        "index.mdx",
        "topic-a/index.mdx",
        "topic-a/page-one.md",
        "topic-b/page-two.mdx",
    ]);
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

test("parseDocFile cleans a blockquote-citation intro (strips > and -- attribution)", () => {
    const PARSE = resolve(__dirname, "__fixtures__", "parse");
    const info = parseDocFile(resolve(PARSE, "quoted.md"), PARSE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.description, "AFFiNE is an open-source, self-hostable workspace.");
});

test("parseDocFile skips a CVE reporter attribution and uses the summary prose", () => {
    const PARSE = resolve(__dirname, "__fixtures__", "parse");
    const info = parseDocFile(resolve(PARSE, "cve.md"), PARSE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(
        info.description,
        "Token reuse in invitation URLs leads to access control bypass via the use of a different enrollment flow.",
    );
});

test("parseDocFile yields no description when the lead content is only a bullet list", () => {
    const PARSE = resolve(__dirname, "__fixtures__", "parse");
    const info = parseDocFile(resolve(PARSE, "prereq-list.md"), PARSE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.description, "");
});

test("parseDocFile strips inline links/emphasis and keeps the first sentence", () => {
    const PARSE = resolve(__dirname, "__fixtures__", "parse");
    const info = parseDocFile(resolve(PARSE, "linky.md"), PARSE);
    assert.ok(info, "non-draft file parses to a record");
    assert.equal(info.description, "The authentik Agent runs on the device.");
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

test("resolveDocumentUrl maps the root index page to /", () => {
    // The site's index.mdx has no trailing "/index" to strip, so its path is the
    // bare "index" — it must still resolve to the site root route.
    assert.equal(resolveDocumentUrl("index", ROUTES), "/");
    assert.equal(resolveDocumentUrl("", ROUTES), "/");
});

test("resolveDocumentUrlFromSource maps routeBasePath and index pages", () => {
    assert.equal(
        resolveDocumentUrlFromSource(testDoc("topic-a/page-one"), "/"),
        "/topic-a/page-one/",
    );
    assert.equal(resolveDocumentUrlFromSource(testDoc("index"), "/"), "/");
    assert.equal(
        resolveDocumentUrlFromSource(testDoc("topic-a/page-one"), "/docs"),
        "/docs/topic-a/page-one/",
    );
});

test("resolveDocumentUrlFromSource honors frontmatter slug overrides", () => {
    assert.equal(
        resolveDocumentUrlFromSource(testDoc("customize/branding", "/branding"), "/"),
        "/branding/",
    );
    assert.equal(
        resolveDocumentUrlFromSource(testDoc("customize/branding", "branding"), "/docs"),
        "/docs/branding/",
    );
});

test("assignGroup always returns the first path segment (slug) for topic grouping", () => {
    const doc = { path: "topic-a/page-one" };
    assert.equal(assignGroup(doc, { groupBy: "topic" }), "topic-a");
});

test("assignGroup always returns the first path segment (slug) for category grouping", () => {
    const doc = { path: "cloud-providers/aws" };
    assert.equal(
        assignGroup(doc, {
            groupBy: "category",
            categories: [["cloud-providers", "Cloud Providers"]],
        }),
        "cloud-providers",
    );
});

test("groupLabel returns the category display label for a known slug", () => {
    assert.equal(
        groupLabel("cloud-providers", {
            groupBy: "category",
            categories: [["cloud-providers", "Cloud Providers"]],
        }),
        "Cloud Providers",
    );
});

test("groupLabel title-cases the slug when no category mapping is found", () => {
    assert.equal(
        groupLabel("unknown-slug", {
            groupBy: "category",
            categories: [["cloud-providers", "Cloud Providers"]],
        }),
        "Unknown Slug",
    );
});

test("groupLabel uses a category label for topic grouping too", () => {
    assert.equal(
        groupLabel("sys-mgmt", {
            groupBy: "topic",
            categories: [["sys-mgmt", "System Management"]],
        }),
        "System Management",
    );
});

test("groupLabel title-cases an unmapped topic slug", () => {
    assert.equal(groupLabel("topic-a", { groupBy: "topic" }), "Topic A");
});

test("assignGroup routes a regrouped subtree to its own slug", () => {
    assert.equal(
        assignGroup(
            { path: "core/glossary" },
            { groupBy: "topic", regroup: [["core/glossary", "glossary"]] },
        ),
        "glossary",
    );
    assert.equal(
        assignGroup(
            { path: "core/glossary/terms/jwt" },
            { groupBy: "topic", regroup: [["core/glossary", "glossary"]] },
        ),
        "glossary",
    );
    assert.equal(
        assignGroup(
            { path: "core/architecture" },
            { groupBy: "topic", regroup: [["core/glossary", "glossary"]] },
        ),
        "core",
    );
});
