import assert from "node:assert/strict";
import { test } from "node:test";

import { destinationToMatcher, pathnameToMatcher, RewriteIndex } from "./index.mjs";

/**
 * @param {Array<[from: string, to: string]>} entries
 */
function createIndex(entries) {
    return new RewriteIndex(entries.map(([from, to]) => ({ from, to, force: true })));
}

//#region Matchers

test("pathnameToMatcher matches exact pathnames only", () => {
    const matcher = pathnameToMatcher("/providers/");

    assert.equal(matcher.test("/providers/"), true);
    assert.equal(matcher.test("/PROVIDERS/"), true, "matching is case-insensitive");
    assert.equal(matcher.test("/providers/ldap/"), false);
    assert.equal(matcher.test("/docs/providers/"), false);
});

test("pathnameToMatcher captures a splat", () => {
    const matcher = pathnameToMatcher("/providers/*");

    const match = matcher.exec("/providers/ldap/create/");

    assert.ok(match?.groups);
    assert.equal(match.groups.splat, "ldap/create/");
});

test("pathnameToMatcher escapes regular expression characters", () => {
    const matcher = pathnameToMatcher("/docs/v2.5/");

    assert.equal(matcher.test("/docs/v2.5/"), true);
    assert.equal(matcher.test("/docs/v2x5/"), false);
});

test("destinationToMatcher captures a splat", () => {
    const matcher = destinationToMatcher("/add-secure-apps/providers/:splat");

    const match = matcher.exec("/add-secure-apps/providers/ldap/");

    assert.ok(match?.groups);
    assert.equal(match.groups.splat, "ldap/");
});

//#endregion

//#region findNextDestination

test("findNextDestination resolves exact redirects", () => {
    const index = createIndex([["/old/", "/new/"]]);

    assert.equal(index.findNextDestination("/old/"), "/new/");
});

test("findNextDestination substitutes splats", () => {
    const index = createIndex([["/providers/*", "/add-secure-apps/providers/:splat"]]);

    assert.equal(
        index.findNextDestination("/providers/ldap/create-ldap-provider/"),
        "/add-secure-apps/providers/ldap/create-ldap-provider/",
    );
});

test("findNextDestination returns the pathname when no rule matches", () => {
    const index = createIndex([["/old/", "/new/"]]);

    assert.equal(index.findNextDestination("/unrelated/"), "/unrelated/");
});

test("findNextDestination uses the first matching rule", () => {
    const index = createIndex([
        ["/old/*", "/first/:splat"],
        ["/old/page/", "/second/"],
    ]);

    assert.equal(index.findNextDestination("/old/page/"), "/first/page/");
});

//#endregion

//#region finalDestination

test("finalDestination follows redirect chains", () => {
    const index = createIndex([
        ["/a/", "/b/"],
        ["/b/", "/c/"],
    ]);

    assert.equal(index.finalDestination("/a/"), "/c/");
});

test("finalDestination terminates on cyclic redirects", () => {
    const index = createIndex([
        ["/a/", "/b/"],
        ["/b/", "/a/"],
    ]);

    assert.equal(index.finalDestination("/a/"), "/b/");
});

test("finalDestination returns an empty pathname unchanged", () => {
    const index = createIndex([["/a/", "/b/"]]);

    assert.equal(index.finalDestination(""), "");
});

//#endregion

//#region findAliases

test("findAliases returns exact sources", () => {
    const index = createIndex([["/old/", "/new/"]]);

    assert.deepEqual(index.findAliases("/new/"), ["/old/"]);
});

test("findAliases substitutes splats back into the source", () => {
    const index = createIndex([["/providers/*", "/add-secure-apps/providers/:splat"]]);

    assert.deepEqual(index.findAliases("/add-secure-apps/providers/ldap/"), ["/providers/ldap/"]);
});

test("findAliases never includes the pathname itself", () => {
    const index = createIndex([
        ["/new/", "/new/"],
        ["/new", "/new/"],
    ]);

    assert.deepEqual(index.findAliases("/new/"), []);
});

test("findAliases deduplicates aliases differing by trailing slashes", () => {
    const index = createIndex([
        ["/old/", "/new/"],
        ["/old", "/new/"],
    ]);

    assert.equal(index.findAliases("/new/").length, 1);
});

test("findAliases handles pathnames of repeated slashes", () => {
    const index = createIndex([["/old/", "/new/"]]);

    assert.deepEqual(index.findAliases("/".repeat(10_000)), []);
});

//#endregion
