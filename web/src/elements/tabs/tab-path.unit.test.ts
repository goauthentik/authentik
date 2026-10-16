import { activeSlotForPath, segmentToSlot, slotToSegment, tabHref } from "./tab-path.js";

import { describe, expect, it } from "vitest";

describe("slot ↔ segment", () => {
    it("round-trips a slot through its segment", () => {
        expect(slotToSegment("page-sessions")).toBe("sessions");
        expect(segmentToSlot("sessions")).toBe("page-sessions");
        expect(slotToSegment(segmentToSlot("oauth-access"))).toBe("oauth-access");
    });
});

describe("activeSlotForPath", () => {
    const settings = ["page-details", "page-sessions", "page-consents", "page-sources"];

    it("returns null when there are no tabs", () => {
        expect(activeSlotForPath("/if/user/settings", "/if/user/settings/sessions", [])).toBeNull();
    });

    it("selects the first tab at the bare base", () => {
        expect(activeSlotForPath("/if/user/settings", "/if/user/settings", settings)).toBe(
            "page-details",
        );
    });

    it("tolerates a trailing slash on the base", () => {
        expect(activeSlotForPath("/if/user/settings/", "/if/user/settings", settings)).toBe(
            "page-details",
        );
    });

    it("selects the tab named by the first segment past the base", () => {
        expect(activeSlotForPath("/if/user/settings", "/if/user/settings/sessions", settings)).toBe(
            "page-sessions",
        );
    });

    it("falls back to the first tab for an unknown segment", () => {
        expect(activeSlotForPath("/if/user/settings", "/if/user/settings/nope", settings)).toBe(
            "page-details",
        );
    });

    it("falls back to the first tab for a path outside the group's subtree", () => {
        expect(activeSlotForPath("/if/user/settings", "/if/user/library", settings)).toBe(
            "page-details",
        );
    });

    it("uses only the first segment, so a nested group owns the rest", () => {
        // The outer group at `/…/users/22` sees `credentials/tokens` and selects
        // credentials; the `tokens` segment belongs to the nested group.
        const outer = ["page-overview", "page-credentials", "page-roles"];

        expect(
            activeSlotForPath(
                "/if/admin/identity/users/22",
                "/if/admin/identity/users/22/credentials/tokens",
                outer,
            ),
        ).toBe("page-credentials");
    });

    it("resolves the nested group from its own deeper base", () => {
        const inner = ["page-sessions", "page-tokens", "page-consent"];

        expect(
            activeSlotForPath(
                "/if/admin/identity/users/22/credentials",
                "/if/admin/identity/users/22/credentials/tokens",
                inner,
            ),
        ).toBe("page-tokens");
    });
});

describe("tabHref", () => {
    const settings = ["page-details", "page-sessions"];
    const [first] = settings;

    it("links the first (default) tab to the bare base", () => {
        expect(tabHref("/if/user/settings", "page-details", first)).toBe("/if/user/settings");
    });

    it("links a non-default tab to base/segment", () => {
        expect(tabHref("/if/user/settings", "page-sessions", first)).toBe(
            "/if/user/settings/sessions",
        );
    });

    it("normalizes a trailing slash on the base", () => {
        expect(tabHref("/if/user/settings/", "page-sessions", first)).toBe(
            "/if/user/settings/sessions",
        );
    });

    it("builds a nested tab href from the deeper base", () => {
        expect(
            tabHref("/if/admin/identity/users/22/credentials", "page-tokens", "page-sessions"),
        ).toBe("/if/admin/identity/users/22/credentials/tokens");
    });
});
