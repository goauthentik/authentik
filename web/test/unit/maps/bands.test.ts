import { bandForZoom, HEX_BANDS } from "#elements/maps/bands";

import { expect, test } from "vitest";

test("bands cover z0-7 contiguously", () => {
    expect(HEX_BANDS.length).toBe(3);
    expect(HEX_BANDS.map((b) => [b.res, b.minzoom, b.maxzoom])).toStrictEqual([
        [3, 0, 2],
        [4, 3, 6],
        [5, 7, 7],
    ]);
});

test("bandForZoom clamps and selects", () => {
    expect(bandForZoom(0).res).toBe(3);
    expect(bandForZoom(2.9).res).toBe(3);
    expect(bandForZoom(3).res).toBe(4);
    expect(bandForZoom(6.5).res).toBe(4);
    expect(bandForZoom(7).res).toBe(5);
    expect(bandForZoom(12).res).toBe(5);
    expect(bandForZoom(-1).res).toBe(3);
});
