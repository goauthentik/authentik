import {
    type AnchorClickContext,
    decideInterception,
    type InterceptScope,
    resolveNavigationMode,
} from "./navigation.js";

import { describe, expect, it } from "vitest";

const scope: InterceptScope = {
    origin: "https://id.example.com",
    base: "/",
    interfaceName: "admin",
    currentPathname: "/if/admin/overview",
    currentSearch: "",
};

function ctx(overrides: Partial<AnchorClickContext> = {}): AnchorClickContext {
    return {
        button: 0,
        metaKey: false,
        ctrlKey: false,
        shiftKey: false,
        altKey: false,
        defaultPrevented: false,
        target: null,
        hasDownload: false,
        href: "https://id.example.com/if/admin/core/applications",
        ...overrides,
    };
}

describe("decideInterception", () => {
    it("claims an unmodified primary-button same-origin in-interface click", () => {
        expect(decideInterception(ctx(), scope)?.pathname).toBe("/if/admin/core/applications");
    });

    it("allows an explicit target=_self", () => {
        expect(decideInterception(ctx({ target: "_self" }), scope)?.pathname).toBe(
            "/if/admin/core/applications",
        );
    });

    it("ignores non-primary mouse buttons", () => {
        expect(decideInterception(ctx({ button: 1 }), scope)).toBeNull();
    });

    it("ignores modified clicks", () => {
        expect(decideInterception(ctx({ metaKey: true }), scope)).toBeNull();
        expect(decideInterception(ctx({ ctrlKey: true }), scope)).toBeNull();
        expect(decideInterception(ctx({ shiftKey: true }), scope)).toBeNull();
        expect(decideInterception(ctx({ altKey: true }), scope)).toBeNull();
    });

    it("ignores already-defaulted clicks", () => {
        expect(decideInterception(ctx({ defaultPrevented: true }), scope)).toBeNull();
    });

    it("ignores target=_blank and download anchors", () => {
        expect(decideInterception(ctx({ target: "_blank" }), scope)).toBeNull();
        expect(decideInterception(ctx({ hasDownload: true }), scope)).toBeNull();
    });

    it("ignores missing hrefs", () => {
        expect(decideInterception(ctx({ href: null }), scope)).toBeNull();
    });

    it("ignores cross-origin links", () => {
        expect(
            decideInterception(ctx({ href: "https://evil.example.com/if/admin/x" }), scope),
        ).toBeNull();
    });

    it("ignores links outside the interface prefix", () => {
        expect(
            decideInterception(ctx({ href: "https://id.example.com/if/user/settings" }), scope),
        ).toBeNull();
        expect(
            decideInterception(ctx({ href: "https://id.example.com/media/x.png" }), scope),
        ).toBeNull();
    });

    it("lets the browser own a hash-only link on the current page", () => {
        expect(
            decideInterception(
                ctx({ href: "https://id.example.com/if/admin/overview#section" }),
                scope,
            ),
        ).toBeNull();
    });

    it("lets the browser own a link to the exact current URL", () => {
        expect(
            decideInterception(ctx({ href: "https://id.example.com/if/admin/overview" }), scope),
        ).toBeNull();
    });

    it("claims a link to the current pathname with a different search", () => {
        expect(
            decideInterception(
                ctx({ href: "https://id.example.com/if/admin/overview?page=2" }),
                scope,
            )?.pathname,
        ).toBe("/if/admin/overview");
    });

    it("respects a non-root base path", () => {
        const authScope: InterceptScope = { ...scope, base: "/auth/" };

        expect(
            decideInterception(ctx({ href: "https://id.example.com/if/admin/x" }), authScope),
        ).toBeNull();
        expect(
            decideInterception(ctx({ href: "https://id.example.com/auth/if/admin/x" }), authScope)
                ?.pathname,
        ).toBe("/auth/if/admin/x");
    });
});

describe("resolveNavigationMode", () => {
    const origin = "https://id.example.com";

    it("keeps push for a same-origin destination", () => {
        expect(resolveNavigationMode("push", origin, origin)).toBe("push");
    });

    it("keeps replace for a same-origin destination", () => {
        expect(resolveNavigationMode("replace", origin, origin)).toBe("replace");
    });

    it("falls back to assign for a cross-origin destination", () => {
        expect(resolveNavigationMode("push", "https://evil.example.com", origin)).toBe("assign");
        expect(resolveNavigationMode("replace", "https://evil.example.com", origin)).toBe("assign");
    });

    it("passes an explicit assign through unchanged", () => {
        expect(resolveNavigationMode("assign", origin, origin)).toBe("assign");
        expect(resolveNavigationMode("assign", "https://evil.example.com", origin)).toBe("assign");
    });
});
