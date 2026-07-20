import assert from "node:assert/strict";
import { latLngToCell } from "h3-js";
import { test } from "node:test";

import { cellCounts } from "../out/hexworld/events.js";

const marker = (id, lat, lon) => ({ id, lat, lon });

test("cellCounts aggregates markers into band-resolution cells", () => {
    const markers = [
        marker("a", 52.52, 13.405),
        marker("b", 52.52, 13.405),
        marker("c", 48.85, 2.35),
    ];
    const counts = cellCounts(markers, 2);
    assert.equal(counts.size, 2);
    assert.equal(counts.get(latLngToCell(52.52, 13.405, 3)), 2);
    assert.equal(counts.get(latLngToCell(48.85, 2.35, 3)), 1);
});

test("cellCounts switches resolution with zoom", () => {
    const markers = [marker("a", 52.52, 13.405), marker("b", 51.34, 12.37)];
    const fine = cellCounts(markers, 8);
    // At z8 each marker lights BOTH its res-5 and its res-4 cell — the
    // archive ships a res-4 base plus a res-5 overlay in the populated zone,
    // and we light both keys so whichever pixel is visible tints correctly.
    // Distant markers separate at both resolutions → 4 entries.
    assert.equal(fine.size, 4, "distant markers light both res-4 base and res-5 overlay");
});

test("cellCounts lights both resolutions per marker at z7-8", () => {
    const markers = [marker("a", 52.52, 13.405)];
    const fine = cellCounts(markers, 8);
    assert.equal(fine.size, 2);
    assert.equal(fine.get(latLngToCell(52.52, 13.405, 5)), 1);
    assert.equal(fine.get(latLngToCell(52.52, 13.405, 4)), 1);
});
