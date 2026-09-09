import { hexFeature, landCells } from "../src/land.ts";
import { required } from "./helpers.ts";

import type { FeatureCollection, MultiPolygon, Polygon } from "geojson";
import { expect, test } from "vitest";

const square = (lng: number, lat: number, d = 4): FeatureCollection<Polygon> => ({
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
    expect(cells.size > 5, `expected >5 res-3 cells, got ${cells.size}`).toBeTruthy();
    const finer = landCells(square(2, 45), 4);
    expect(finer.size > cells.size * 4, "res 4 should be much denser than res 3").toBeTruthy();
});

test("landCells handles MultiPolygon and dedupes across features", () => {
    const base = square(2, 45);
    const seed = required(base.features[0], "seed feature");
    const fc: FeatureCollection<Polygon | MultiPolygon> = {
        ...base,
        features: [
            ...base.features,
            {
                type: "Feature",
                properties: {},
                geometry: { type: "MultiPolygon", coordinates: [seed.geometry.coordinates] },
            },
        ],
    };
    expect(landCells(fc, 3).size).toBe(landCells(square(2, 45), 3).size);
});

test("hexFeature carries the cell id as the correlation key", () => {
    const cell = required([...landCells(square(2, 45), 3)][0], "a land cell");
    const feature = hexFeature(cell);
    expect(required(feature.properties, "hex properties").h3).toBe(cell);
    expect(feature.geometry.type).toBe("Polygon");
});

// Antarctica-shaped polygon: full longitude span, southern latitudes below the
// web-mercator floor. h3's polygonToCells throws E_FAILED on rings wider than
// 180 deg (transmeridian ambiguity), and Natural Earth draws Antarctica down
// to lat -89.9989 with a seam edge along the antimeridian.
const antarcticaLike = (): FeatureCollection<Polygon> => ({
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
        expect(cells.size > 0, `expected cells at res ${res}, got ${cells.size}`).toBeTruthy();
    }
});

test("landCells is stable across runs for a split polygon (no seam dupes)", () => {
    const a = landCells(antarcticaLike(), 4);
    const b = landCells(antarcticaLike(), 4);
    expect(a.size).toBe(b.size);
    for (const cell of a) expect(b.has(cell), "cell drifted between runs").toBeTruthy();
});
