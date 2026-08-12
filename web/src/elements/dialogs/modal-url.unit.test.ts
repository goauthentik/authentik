import { resolveModalCloseURL } from "./modal-url.js";

import { describe, expect, it } from "vitest";

const ORIGIN = "https://id.example.com";

describe("resolveModalCloseURL", () => {
    it("reverts search params written by slotted content while the modal was open", () => {
        expect(
            resolveModalCloseURL(
                `${ORIGIN}/if/admin/core/providers`,
                `${ORIGIN}/if/admin/core/providers?ak-provider-list-page=2`,
                [],
            ),
        ).toBe(`${ORIGIN}/if/admin/core/providers`);
    });

    it("strips the modal's own declared params, even when present on open", () => {
        // A deep-link/trigger param that opened the modal must not survive close,
        // or the modal would re-open on reload.
        expect(
            resolveModalCloseURL(
                `${ORIGIN}/if/admin/core/providers?type=oauth2`,
                `${ORIGIN}/if/admin/core/providers?type=oauth2`,
                ["type"],
            ),
        ).toBe(`${ORIGIN}/if/admin/core/providers`);
    });

    it("leaves params it does not own", () => {
        expect(
            resolveModalCloseURL(
                `${ORIGIN}/if/admin/core/providers?keep=1`,
                `${ORIGIN}/if/admin/core/providers?keep=1&type=oauth2`,
                ["type"],
            ),
        ).toBe(`${ORIGIN}/if/admin/core/providers?keep=1`);
    });

    it("returns null when the modal navigated to a different path", () => {
        expect(
            resolveModalCloseURL(
                `${ORIGIN}/if/admin/core/providers`,
                `${ORIGIN}/if/admin/core/providers/42`,
                [],
            ),
        ).toBeNull();
    });

    it("returns null when nothing changed", () => {
        expect(
            resolveModalCloseURL(
                `${ORIGIN}/if/admin/core/providers`,
                `${ORIGIN}/if/admin/core/providers`,
                [],
            ),
        ).toBeNull();
    });
});
