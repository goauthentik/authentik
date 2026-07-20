import assert from "node:assert/strict";
import { test } from "node:test";

import { HEX_BANDS, bandForZoom } from "../out/hexworld/bands.js";

test("bands cover z0-8 contiguously", () => {
    assert.equal(HEX_BANDS.length, 3);
    assert.deepEqual(
        HEX_BANDS.map((b) => [b.res, b.minzoom, b.maxzoom]),
        [
            [3, 0, 2],
            [4, 3, 6],
            [5, 7, 7],
        ],
    );
});

test("bandForZoom clamps and selects", () => {
    assert.equal(bandForZoom(0).res, 3);
    assert.equal(bandForZoom(2.9).res, 3);
    assert.equal(bandForZoom(3).res, 4);
    assert.equal(bandForZoom(6.5).res, 4);
    assert.equal(bandForZoom(7).res, 5);
    assert.equal(bandForZoom(12).res, 5);
    assert.equal(bandForZoom(-1).res, 3);
});
