import assert from "node:assert/strict";
import { latLngToCell } from "h3-js";
import { test } from "node:test";

import { assignCountries, buildCountryIndex } from "../out/hexworld/countries.js";

const rectangle = (lngMin, latMin, lngMax, latMax) => [
    [lngMin, latMin],
    [lngMax, latMin],
    [lngMax, latMax],
    [lngMin, latMax],
    [lngMin, latMin],
];

const countryFC = () => ({
    type: "FeatureCollection",
    features: [
        {
            type: "Feature",
            properties: { ISO_A2: "AA" },
            geometry: { type: "Polygon", coordinates: [rectangle(-10, -10, 0, 10)] },
        },
        {
            type: "Feature",
            properties: { ISO_A2: "BB" },
            geometry: { type: "Polygon", coordinates: [rectangle(0, -10, 10, 10)] },
        },
        {
            type: "Feature",
            properties: { ISO_A2: "CC" },
            geometry: {
                type: "MultiPolygon",
                coordinates: [[rectangle(20, 20, 30, 30)], [rectangle(40, 40, 50, 50)]],
            },
        },
    ],
});

test("assignCountries labels cells whose center lies in a country", () => {
    const index = buildCountryIndex(countryFC());
    const cells = new Set([
        latLngToCell(0, -5, 4), // in AA
        latLngToCell(0, 5, 4), // in BB
        latLngToCell(25, 25, 4), // in CC first polygon
        latLngToCell(45, 45, 4), // in CC second polygon
        latLngToCell(0, 100, 4), // north pole, off any country
    ]);
    const assigned = assignCountries(cells, index);
    assert.equal(assigned.get(latLngToCell(0, -5, 4)), "AA");
    assert.equal(assigned.get(latLngToCell(0, 5, 4)), "BB");
    assert.equal(assigned.get(latLngToCell(25, 25, 4)), "CC");
    assert.equal(assigned.get(latLngToCell(45, 45, 4)), "CC");
    assert.equal(assigned.has(latLngToCell(0, 100, 4)), false);
});

test("assignCountries respects the bbox prefilter (skips far-away polygons)", () => {
    const index = buildCountryIndex(countryFC());
    // Cell far from every rectangle; should return no entry, not throw.
    const cell = latLngToCell(-80, 170, 4);
    const assigned = assignCountries(new Set([cell]), index);
    assert.equal(assigned.has(cell), false);
});

test("buildCountryIndex prefers ISO_A2, falls back to iso_a2 or ADM0_A3", () => {
    const index = buildCountryIndex({
        type: "FeatureCollection",
        features: [
            {
                type: "Feature",
                properties: { iso_a2: "XX" },
                geometry: { type: "Polygon", coordinates: [rectangle(-1, -1, 1, 1)] },
            },
            {
                type: "Feature",
                properties: { ADM0_A3: "YYY" },
                geometry: { type: "Polygon", coordinates: [rectangle(9, 9, 11, 11)] },
            },
        ],
    });
    const cellA = latLngToCell(0, 0, 4);
    const cellB = latLngToCell(10, 10, 4);
    const assigned = assignCountries(new Set([cellA, cellB]), index);
    assert.equal(assigned.get(cellA), "XX");
    assert.equal(assigned.get(cellB), "YYY");
});
