import assert from "node:assert/strict";
import { test } from "node:test";

import { LLMS_FULL_FILENAME, LLMS_TXT_FILENAME, normalizeOptions } from "./common.mjs";

test("filename constants follow llmstxt.org convention", () => {
    assert.equal(LLMS_TXT_FILENAME, "llms.txt");
    assert.equal(LLMS_FULL_FILENAME, "llms-full.txt");
});

test("normalizeOptions applies defaults", () => {
    const opts = normalizeOptions({ sections: [{ path: ".", routeBasePath: "/" }] });
    assert.deepEqual(opts.ignoreFiles, []);
    assert.equal(opts.groupBy, "topic");
    assert.deepEqual(opts.crossLinks, []);
});

test("normalizeOptions throws without sections", () => {
    assert.throws(() => normalizeOptions({}), /sections/);
});

test("normalizeOptions throws with empty sections array", () => {
    assert.throws(() => normalizeOptions({ sections: [] }), /sections/);
});
