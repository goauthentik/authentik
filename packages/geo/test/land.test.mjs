import assert from "node:assert/strict";
import { test } from "node:test";

import { hexFeature, landCells } from "../out/hexworld/land.js";

const square = (lng, lat, d = 4) => ({
    type: "FeatureCollection",
    features: [
        {
            type: "Feature",
            properties: {},
            geometry: {
                type: "Polygon",
                coordinates: [
                    [
                        [lng, lat],
                        [lng + d, lat],
                        [lng + d, lat + d],
                        [lng, lat + d],
                        [lng, lat],
                    ],
                ],
            },
        },
    ],
});

test("landCells fills a polygon at the requested resolution", () => {
    const cells = landCells(square(2, 45), 3);
    assert.ok(cells.size > 5, `expected >5 res-3 cells, got ${cells.size}`);
    const finer = landCells(square(2, 45), 4);
    assert.ok(finer.size > cells.size * 4, "res 4 should be much denser than res 3");
});

test("landCells handles MultiPolygon and dedupes across features", () => {
    const fc = square(2, 45);
    fc.features.push({
        type: "Feature",
        properties: {},
        geometry: {
            type: "MultiPolygon",
            coordinates: [fc.features[0].geometry.coordinates],
        },
    });
    assert.equal(landCells(fc, 3).size, landCells(square(2, 45), 3).size);
});

test("hexFeature carries the cell id as the correlation key", () => {
    const [cell] = landCells(square(2, 45), 3);
    const feature = hexFeature(cell);
    assert.equal(feature.properties.h3, cell);
    assert.equal(feature.geometry.type, "Polygon");
});

// Antarctica-shaped polygon: full longitude span, southern latitudes below the
// web-mercator floor. h3's polygonToCells throws E_FAILED on rings wider than
// 180 deg (transmeridian ambiguity), and Natural Earth draws Antarctica down
// to lat -89.9989 with a seam edge along the antimeridian.
const antarcticaLike = () => ({
    type: "FeatureCollection",
    features: [
        {
            type: "Feature",
            properties: {},
            geometry: {
                type: "Polygon",
                coordinates: [
                    [
                        [-180, -65],
                        [180, -65],
                        [180, -89.9989],
                        [-180, -89.9989],
                        [-180, -65],
                    ],
                ],
            },
        },
    ],
});

test("landCells polyfills a transmeridian polygon at every band", () => {
    for (const res of [3, 4, 5]) {
        const cells = landCells(antarcticaLike(), res);
        assert.ok(cells.size > 0, `expected cells at res ${res}, got ${cells.size}`);
    }
});

test("landCells is stable across runs for a split polygon (no seam dupes)", () => {
    const a = landCells(antarcticaLike(), 4);
    const b = landCells(antarcticaLike(), 4);
    assert.equal(a.size, b.size);
    for (const cell of a) assert.ok(b.has(cell), "cell drifted between runs");
});
