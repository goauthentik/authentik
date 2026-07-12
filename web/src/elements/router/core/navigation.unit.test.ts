import { type AnchorClickContext, decideInterception, type InterceptScope } from "./navigation.js";

import { describe, expect, it } from "vitest";

const scope: InterceptScope = {
    origin: "https://id.example.com",
    base: "/",
    interfaceName: "admin",
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
