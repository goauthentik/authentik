import assert from "node:assert/strict";
import { test } from "node:test";

import { cellPolygon } from "../out/hexworld/cells.js";

import { latLngToCell } from "h3-js";

test("cellPolygon returns a closed ring", () => {
    const cell = latLngToCell(52.52, 13.405, 3);
    const poly = cellPolygon(cell);
    assert.equal(poly.type, "Polygon");
    const ring = poly.coordinates[0];
    assert.ok(ring.length >= 7);
    assert.deepEqual(ring[0], ring[ring.length - 1]);
});

test("cellPolygon does not span the antimeridian", () => {
    const cell = latLngToCell(-16.5, 179.9, 3);
    const ring = cellPolygon(cell).coordinates[0];
    const lngs = ring.map(([lng]) => lng);
    assert.ok(Math.max(...lngs) - Math.min(...lngs) < 180);
});
