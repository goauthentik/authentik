import { cellPolygon } from "../src/cells.ts";

import { latLngToCell } from "h3-js";
import { expect, test } from "vitest";

test("cellPolygon returns a closed ring", () => {
    const cell = latLngToCell(52.52, 13.405, 3);
    const poly = cellPolygon(cell);
    expect(poly.type).toBe("Polygon");
    const ring = poly.coordinates[0];
    expect(ring.length >= 7).toBeTruthy();
    expect(ring[0]).toStrictEqual(ring[ring.length - 1]);
});

test("cellPolygon does not span the antimeridian", () => {
    const cell = latLngToCell(-16.5, 179.9, 3);
    const ring = cellPolygon(cell).coordinates[0];
    const lngs = ring.map(([lng]) => lng);
    expect(Math.max(...lngs) - Math.min(...lngs) < 180).toBeTruthy();
});
