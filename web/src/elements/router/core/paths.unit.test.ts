import {
    ensureTrailingSlash,
    joinPath,
    stripLeadingSlash,
    stripPrefix,
    stripTrailingSlash,
} from "./paths.js";

import { describe, expect, test } from "vitest";

describe("stripLeadingSlash", () => {
    test("drops one or many leading slashes", () => {
        expect(stripLeadingSlash("/settings")).toBe("settings");
        expect(stripLeadingSlash("///settings")).toBe("settings");
    });

    test("leaves a bare segment and the empty string alone", () => {
        expect(stripLeadingSlash("settings")).toBe("settings");
        expect(stripLeadingSlash("")).toBe("");
    });

    test("does not touch a trailing slash", () => {
        expect(stripLeadingSlash("/settings/")).toBe("settings/");
    });
});

describe("stripTrailingSlash", () => {
    test("drops one or many trailing slashes", () => {
        expect(stripTrailingSlash("/if/user/")).toBe("/if/user");
        expect(stripTrailingSlash("/if/user///")).toBe("/if/user");
    });

    test("reduces root to the empty string", () => {
        expect(stripTrailingSlash("/")).toBe("");
    });
});

describe("ensureTrailingSlash", () => {
    test("adds a slash only when one is missing", () => {
        expect(ensureTrailingSlash("/auth")).toBe("/auth/");
        expect(ensureTrailingSlash("/auth/")).toBe("/auth/");
    });
});

describe("joinPath", () => {
    test("produces exactly one separator whatever the inputs carry", () => {
        expect(joinPath("/if/user", "settings")).toBe("/if/user/settings");
        expect(joinPath("/if/user/", "settings")).toBe("/if/user/settings");
        expect(joinPath("/if/user", "/settings")).toBe("/if/user/settings");
        expect(joinPath("/if/user/", "/settings")).toBe("/if/user/settings");
    });

    test("joins onto a root prefix without doubling", () => {
        expect(joinPath("/", "settings")).toBe("/settings");
        expect(joinPath("/", "/settings")).toBe("/settings");
    });
});

describe("stripPrefix", () => {
    test("strips the prefix and keeps the leading slash", () => {
        expect(stripPrefix("/if/user/settings", "/if/user/")).toBe("/settings");
        expect(stripPrefix("/if/user/settings", "/if/user")).toBe("/settings");
    });

    test("maps the prefix itself to root, with or without its trailing slash", () => {
        expect(stripPrefix("/if/user/", "/if/user/")).toBe("/");
        expect(stripPrefix("/if/user", "/if/user/")).toBe("/");
    });

    test("matches whole segments, not shared text", () => {
        // The nested-outlet case: a sibling whose path merely starts with the
        // base must not be treated as living under it.
        expect(stripPrefix("/if/user/users/220", "/if/user/users/22")).toBe("/if/user/users/220");
        expect(stripPrefix("/if/user/users/22/tab", "/if/user/users/22")).toBe("/tab");
    });

    test("passes a pathname outside the prefix through untouched", () => {
        // The outlet relies on this to fall through to its 404 branch.
        expect(stripPrefix("/if/admin/overview", "/if/user/")).toBe("/if/admin/overview");
    });

    test("handles a base-path deployment", () => {
        expect(stripPrefix("/auth/if/admin/flow/stages", "/auth/if/admin/")).toBe("/flow/stages");
    });
});
